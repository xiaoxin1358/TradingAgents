import { defineStore } from "pinia";
import { fetchContradictions } from "../api";
import type { ContradictionFilters } from "../api";
import type { ContradictionRow } from "../api/types";

interface State {
  filters: ContradictionFilters;
  rows: ContradictionRow[];
  total: number;
  loading: boolean;
  selected: ContradictionRow | null;
}

export const useContradictionStore = defineStore("contradictions", {
  state: (): State => ({
    filters: { status: "open" },
    rows: [],
    total: 0,
    loading: false,
    selected: null,
  }),
  actions: {
    async load() {
      this.loading = true;
      try {
        const res = await fetchContradictions(this.filters);
        this.rows = res.rows;
        this.total = res.total;
      } finally {
        this.loading = false;
      }
    },
    setFilter(
      key: keyof ContradictionFilters,
      value: string | number | null | undefined,
    ) {
      (this.filters as Record<string, unknown>)[key] = value;
    },
    async openDetail(id: string) {
      const { fetchContradictionDetail } = await import("../api");
      this.selected = await fetchContradictionDetail(id);
    },
    closeDetail() {
      this.selected = null;
    },
  },
});
