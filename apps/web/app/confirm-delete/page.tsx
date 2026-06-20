import { ConfirmDeleteView } from "./confirm-delete-view";

export default function ConfirmDeletePage({ searchParams }: { searchParams: { token?: string } }) {
  const token = typeof searchParams.token === "string" ? searchParams.token : null;
  return <ConfirmDeleteView token={token} />;
}
