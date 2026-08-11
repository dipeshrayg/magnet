import hashlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..models import AppUser, GrowthEvent, Referral
from ..serialize import to_dict, to_list
from ..workspace_ctx import WorkspaceContext, get_workspace_ctx

router = APIRouter(tags=["referrals"])

REWARD_TIERS = [(1, "1 month free"), (5, "3 months free"), (10, "lifetime discount")]


@router.get("/workspaces/{workspace_id}/referrals")
def list_referrals(ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    return to_list(ctx.query(Referral).order_by(Referral.position).all())


class ReferralRequest(BaseModel):
    referrer_user_id: int


@router.post("/workspaces/{workspace_id}/referrals/link")
def create_referral_link(body: ReferralRequest, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    user = ctx.get_or_404(AppUser, body.referrer_user_id)
    code = hashlib.sha1(f"{ctx.workspace_id}-{user.id}".encode()).hexdigest()[:8]
    existing = ctx.query(Referral).filter(Referral.referrer_user_id == user.id, Referral.referred_email == "").first()
    if existing:
        return to_dict(existing)
    ref = Referral(code=code, referrer_user_id=user.id, position=ctx.query(Referral).count() + 1)
    ctx.add(ref)
    ctx.db.commit()
    return {"referral": to_dict(ref), "share_url": f"https://magnet.local/r/{code}"}


class ReferralSignupRequest(BaseModel):
    code: str
    referred_email: str


@router.post("/workspaces/{workspace_id}/referrals/signup")
def referral_signup(body: ReferralSignupRequest, ctx: WorkspaceContext = Depends(get_workspace_ctx)):
    """Attributes a signup to the referral code and creates the growth event."""
    referrer_link = ctx.query(Referral).filter(Referral.code == body.code).first()
    referral_count = ctx.query(Referral).filter(Referral.referred_email != "").count()
    reward = next((r for tier, r in reversed(REWARD_TIERS) if referral_count + 1 >= tier), "")
    entry = Referral(
        code=body.code,
        referrer_user_id=referrer_link.referrer_user_id if referrer_link else None,
        referred_email=body.referred_email,
        position=referral_count + 1,
        reward=reward,
    )
    ctx.add(entry)
    ctx.add(GrowthEvent(stage="signup", source_module="M11 Referrals", attribution_source=f"referral:{body.code}"))
    ctx.db.commit()
    return to_dict(entry)
