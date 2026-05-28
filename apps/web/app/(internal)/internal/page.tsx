import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function InternalDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Internal Dashboard</h1>
        <p className="text-muted-foreground">Platform operations and tenant management.</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Overview</CardTitle>
          <CardDescription>Cross-tenant tools for internal staff.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            Tenant management, sales tools, and support views will appear here in upcoming releases.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
