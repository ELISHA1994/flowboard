'use client';

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
} from 'recharts';
import { ChartContainer } from './chart-container';

interface DataPoint {
  [key: string]: string | number;
}

interface BarChartComponentProps {
  title: string;
  description?: string;
  data: DataPoint[];
  dataKeys: {
    key: string;
    name: string;
    color: string;
  }[];
  xAxisKey: string;
  height?: number;
  isLoading?: boolean;
  error?: Error | null;
  orientation?: 'vertical' | 'horizontal';
  showGrid?: boolean;
  showLegend?: boolean;
  formatXAxis?: (value: any) => string;
  formatYAxis?: (value: any) => string;
  formatTooltip?: (value: any, name: string) => [string, string];
}

export function BarChartComponent({
  title,
  description,
  data,
  dataKeys,
  xAxisKey,
  height = 300,
  isLoading = false,
  error = null,
  orientation = 'vertical',
  showGrid = true,
  showLegend = false,
  formatXAxis,
  formatYAxis,
  formatTooltip,
}: BarChartComponentProps) {
  return (
    <ChartContainer title={title} description={description} isLoading={isLoading} error={error}>
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout={orientation === 'horizontal' ? 'horizontal' : undefined}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
            {orientation === 'vertical' ? (
              <>
                <XAxis
                  dataKey={xAxisKey}
                  tickFormatter={formatXAxis}
                  className="text-xs"
                  tick={{ fontSize: 12 }}
                />
                <YAxis tickFormatter={formatYAxis} className="text-xs" tick={{ fontSize: 12 }} />
              </>
            ) : (
              <>
                <XAxis
                  type="number"
                  tickFormatter={formatYAxis}
                  className="text-xs"
                  tick={{ fontSize: 12 }}
                />
                <YAxis
                  type="category"
                  dataKey={xAxisKey}
                  tickFormatter={formatXAxis}
                  className="text-xs"
                  tick={{ fontSize: 12 }}
                  width={100}
                />
              </>
            )}
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={formatTooltip}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            {showLegend && <Legend wrapperStyle={{ paddingTop: '20px' }} />}
            {dataKeys.map((item) => (
              <Bar
                key={item.key}
                dataKey={item.key}
                fill={item.color}
                name={item.name}
                radius={4}
              />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}

// Specialized category distribution chart
export function CategoryDistributionChart({
  data,
  isLoading,
  error,
}: {
  data: Array<{
    category_id: string;
    category_name: string;
    color: string;
    task_count: number;
  }>;
  isLoading?: boolean;
  error?: Error | null;
}) {
  const chartData = data.map((item) => ({
    name: item.category_name,
    count: item.task_count,
    color: item.color,
  }));

  return (
    <ChartContainer
      title="Tasks by Category"
      description="Distribution of tasks across categories"
      isLoading={isLoading}
      error={error}
    >
      <div style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="horizontal"
            margin={{ top: 20, right: 30, left: 100, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis type="number" className="text-xs" tick={{ fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="name"
              className="text-xs"
              tick={{ fontSize: 12 }}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value) => [`${value} tasks`, 'Count']}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Bar dataKey="count" radius={4}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}

// Specialized tag distribution chart
export function TagDistributionChart({
  data,
  isLoading,
  error,
}: {
  data: Array<{
    tag_id: string;
    tag_name: string;
    color: string;
    task_count: number;
  }>;
  isLoading?: boolean;
  error?: Error | null;
}) {
  // Show only top 10 tags
  const sortedData = data.sort((a, b) => b.task_count - a.task_count).slice(0, 10);

  const chartData = sortedData.map((item) => ({
    name: item.tag_name,
    count: item.task_count,
    color: item.color,
  }));

  return (
    <ChartContainer
      title="Top Tags"
      description="Most frequently used tags"
      isLoading={isLoading}
      error={error}
    >
      <div style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="name"
              className="text-xs"
              tick={{ fontSize: 10 }}
              angle={-45}
              textAnchor="end"
              height={60}
            />
            <YAxis className="text-xs" tick={{ fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: 'hsl(var(--card))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              }}
              formatter={(value) => [`${value} tasks`, 'Count']}
              labelStyle={{ color: 'hsl(var(--foreground))' }}
            />
            <Bar dataKey="count" radius={4}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  );
}
