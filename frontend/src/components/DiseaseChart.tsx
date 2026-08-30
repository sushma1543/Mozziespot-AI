import { Bar } from "react-chartjs-2";
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip
} from "chart.js";
import { Detection } from "../lib/api";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export function DiseaseChart({ detection }: { detection: Detection }) {
  const diseaseIndex = detection.advanced_disease_index ?? detection.disease_index;
  const labels = Object.keys(diseaseIndex);
  return (
    <Bar
      data={{
        labels,
        datasets: [
          {
            label: "Suitability",
            data: labels.map((key) => diseaseIndex[key]),
            backgroundColor: ["#d64f4f", "#2b8a67", "#f08a24", "#7c5cc4", "#4098d7", "#6b7280"],
            borderRadius: 5
          }
        ]
      }}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { min: 0, max: 100 } },
        plugins: { legend: { display: false } }
      }}
    />
  );
}
