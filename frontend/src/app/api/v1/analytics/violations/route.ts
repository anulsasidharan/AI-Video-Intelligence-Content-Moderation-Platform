import { NextResponse } from 'next/server';

export async function GET() {
  const days = 30;
  const today = new Date('2026-03-17');

  const timeSeries = Array.from({ length: days }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() - (days - 1 - i));
    return {
      date: d.toISOString().slice(0, 10),
      count: Math.floor(Math.random() * 18) + 2,
    };
  });

  return NextResponse.json({
    data: {
      time_series: timeSeries,
      breakdown: [
        { category: 'violence', count: 58, rate: 0.045 },
        { category: 'nudity', count: 41, rate: 0.032 },
        { category: 'hate_symbols', count: 27, rate: 0.021 },
        { category: 'drugs', count: 19, rate: 0.015 },
        { category: 'misinformation', count: 14, rate: 0.011 },
        { category: 'spam', count: 8, rate: 0.006 },
        { category: 'other', count: 3, rate: 0.002 },
      ],
    },
  });
}
