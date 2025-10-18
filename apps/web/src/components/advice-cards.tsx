import { Lightbulb, TrendingDown, Clock } from "lucide-react";

interface Advice {
  id: string;
  title: string;
  text: string;
  savings_est_usd: number;
  co2_saved_kg: number;
  type: string;
}

interface AdviceCardsProps {
  advice: Advice[];
}

const typeIcons = {
  peak_management: Clock,
  efficiency: TrendingDown,
  off_hours: Lightbulb,
};

const typeColors = {
  peak_management: "bg-orange-50 text-orange-600",
  efficiency: "bg-blue-50 text-blue-600",
  off_hours: "bg-purple-50 text-purple-600",
};

export function AdviceCards({ advice }: AdviceCardsProps) {
  if (!advice || advice.length === 0) {
    return (
      <div className="rounded-lg border bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">AI Recommendations</h2>
        <p className="text-gray-500">
          No recommendations available. Check back soon!
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-semibold">AI Recommendations</h2>
      
      <div className="space-y-4">
        {advice.map((item) => {
          const Icon = typeIcons[item.type as keyof typeof typeIcons] || Lightbulb;
          const colorClass = typeColors[item.type as keyof typeof typeColors] || "bg-gray-50 text-gray-600";
          
          return (
            <div
              key={item.id}
              className="flex gap-4 rounded-lg border p-4 transition-shadow hover:shadow-md"
            >
              <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg ${colorClass}`}>
                <Icon className="h-5 w-5" />
              </div>
              
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900">{item.title}</h3>
                <p className="mt-1 text-sm text-gray-600">{item.text}</p>
                
                <div className="mt-3 flex gap-4 text-xs text-gray-500">
                  <span className="font-medium text-green-600">
                    💰 ${item.savings_est_usd.toFixed(2)}/day
                  </span>
                  <span className="font-medium text-emerald-600">
                    🌱 {item.co2_saved_kg.toFixed(1)} kg CO₂
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
