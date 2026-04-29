import { ProspectTable } from "@/components/prospect-table";

export default function ProspectsPage() {
  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Prospects</h1>
        <p className="text-sm text-zinc-500">
          Filter, sort, and inspect cached prospects.
        </p>
      </div>
      <ProspectTable />
    </div>
  );
}
