import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./Layout";
import Portfolio from "./pages/Portfolio";
import AddProduct from "./pages/AddProduct";
import Dashboard from "./pages/Dashboard";
import Icp from "./pages/Icp";
import LeadRadar from "./pages/LeadRadar";
import CompetitorWatch from "./pages/CompetitorWatch";
import Reputation from "./pages/Reputation";
import PseoFactory from "./pages/PseoFactory";
import FreeTool from "./pages/FreeTool";
import ContentStudio from "./pages/ContentStudio";
import Outreach from "./pages/Outreach";
import Lifecycle from "./pages/Lifecycle";
import Voc from "./pages/Voc";
import Referrals from "./pages/Referrals";
import Analytics from "./pages/Analytics";
import ApprovalInbox from "./pages/ApprovalInbox";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Portfolio />} />
        <Route path="/add" element={<AddProduct />} />
        <Route path="/w/:workspaceId" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="icp" element={<Icp />} />
          <Route path="leads" element={<LeadRadar />} />
          <Route path="competitors" element={<CompetitorWatch />} />
          <Route path="pseo" element={<PseoFactory />} />
          <Route path="reputation" element={<Reputation />} />
          <Route path="freetool" element={<FreeTool />} />
          <Route path="content" element={<ContentStudio />} />
          <Route path="outreach" element={<Outreach />} />
          <Route path="lifecycle" element={<Lifecycle />} />
          <Route path="voc" element={<Voc />} />
          <Route path="referrals" element={<Referrals />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="approvals" element={<ApprovalInbox />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
