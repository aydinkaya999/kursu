export type DataTableProps = {
  label: string;
  headers: readonly string[];
  rows: readonly (readonly string[])[];
  highlightedColumn?: number;
};
