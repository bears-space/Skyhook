<script setup lang="ts">
import type {
  ColumnDef,
  ColumnFiltersState,
  SortingState,
} from "@tanstack/vue-table"
import {
  FlexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useVueTable,
} from "@tanstack/vue-table"
import { computed, ref } from "vue"
import { ArrowUpDown } from "lucide-vue-next"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableEmpty,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { valueUpdater } from "@/components/ui/table/utils"

type DataTableProps<TData> = {
  columns: ColumnDef<TData, any>[]
  data: TData[]
  filterColumn?: string
  searchPlaceholder?: string
}

const props = defineProps<DataTableProps<any>>()

const sorting = ref<SortingState>([])
const columnFilters = ref<ColumnFiltersState>([])

const table = useVueTable({
  get data() {
    return props.data
  },
  get columns() {
    return props.columns
  },
  state: {
    get sorting() {
      return sorting.value
    },
    get columnFilters() {
      return columnFilters.value
    },
  },
  onSortingChange: (updater) => valueUpdater(updater, sorting),
  onColumnFiltersChange: (updater) => valueUpdater(updater, columnFilters),
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getFilteredRowModel: getFilteredRowModel(),
})

const filterColumn = computed(() => {
  const key =
    props.filterColumn ||
    props.columns[0]?.id ||
    (props.columns[0] as any)?.accessorKey ||
    ""
  return key ? table.getColumn(key) : undefined
})
</script>

<template>
  <div class="space-y-3">
    <div v-if="filterColumn" class="flex items-center gap-2">
      <Input
        class="w-full max-w-sm"
        :placeholder="searchPlaceholder || 'Search...'"
        :model-value="(filterColumn.getFilterValue() as string) ?? ''"
        @input="filterColumn.setFilterValue($event.target.value)"
      />
      <Button
        v-if="(filterColumn.getFilterValue() as string) || ''"
        variant="ghost"
        size="sm"
        @click="filterColumn.setFilterValue('')"
      >
        Clear
      </Button>
    </div>

    <div class="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="align-middle"
            >
              <span v-if="header.isPlaceholder">&nbsp;</span>
              <Button
                v-else
                variant="ghost"
                class="flex w-full items-center justify-between px-2 py-0 text-left font-semibold"
                :disabled="!header.column.getCanSort()"
                @click="header.column.toggleSorting(header.column.getIsSorted() === 'asc')"
              >
                <span class="truncate">
                  <FlexRender :render="header.column.columnDef.header" :props="header.getContext()" />
                </span>
                <ArrowUpDown class="ml-2 h-3.5 w-3.5 text-muted-foreground" />
              </Button>
            </TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          <template v-if="table.getRowModel().rows.length">
            <TableRow v-for="row in table.getRowModel().rows" :key="row.id">
              <TableCell
                v-for="cell in row.getVisibleCells()"
                :key="cell.id"
                class="align-middle"
              >
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
          </template>
          <TableEmpty v-else :colspan="table.getAllColumns().length">
            No results for this filter.
          </TableEmpty>
        </TableBody>
      </Table>
    </div>
  </div>
</template>
