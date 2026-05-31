import { LandingPage } from "@/components/landing-page/landing-page";
import { landingPageMetadata } from "@/components/landing-page/seo";

export const metadata = landingPageMetadata;

export default function HomePage() {
  return <LandingPage />;
}
