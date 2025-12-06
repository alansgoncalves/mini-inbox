import { fetchMetrics } from "@/lib/services";
import { Metrics } from "@/lib/types";

interface DailyTicketCount {
    date: string;
    count: number;
}
interface YearlyTicketCount {
    year: number;
    count: number;
}

// --- FUNÇÃO DE AGREGAÇÃO (Movemos para o topo da página) ---
function aggregateByYear(dailyData: DailyTicketCount[]): YearlyTicketCount[] {
    const yearlyMap = dailyData.reduce((acc, item) => {
        const year = new Date(item.date).getFullYear();
        acc.set(year, (acc.get(year) || 0) + item.count);
        return acc;
    }, new Map<number, number>());

    // Converte o Map em um array de objetos, ordenado pelo ano
return Array.from(yearlyMap.entries())
        .map(([year, count]) => ({ year, count }))
        .sort((a, b) => b.year - a.year);
}

const StatCard = ({ title, value }: { title: string; value: string | number }) => (
  <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100">
    <p className="text-sm font-medium text-gray-500">{title}</p>
    <p className="mt-1 text-3xl font-semibold text-indigo-600">{value}</p>
  </div>
);

const TopItemsList = ({ title, data }: { title: string; data: Record<string, number> }) => (
  <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100 mt-6">
    <h3 className="text-lg font-semibold text-gray-800 mb-4">{title}</h3>
    <dl className="space-y-2">
      {Object.entries(data)
        .sort(([, countA], [, countB]) => countB - countA) // Ordena por contagem
        .map(([name, count]) => (
          <div key={name} className="flex justify-between border-b pb-1">
            <dt className="text-sm text-gray-600">{name}</dt>
            <dd className="text-sm font-medium text-gray-900">{count.toLocaleString('pt-BR')}</dd>
          </div>
        ))}
    </dl>
  </div>
);

const YearlyTicketsCard = ({ data }: { data: YearlyTicketCount[] }) => (
    <div className="bg-white p-6 rounded-lg shadow-md border border-gray-100 mt-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">Top 5 Tickets Abertos por Ano</h2>
        <dl className="space-y-2">
            {data.slice(0, 5).map(({ year, count }) => (
                <div key={year} className="flex justify-between border-b pb-1">
                    <dt className="text-sm font-medium text-gray-600">{year}</dt>
                    <dd className="text-sm font-medium text-gray-900">{count.toLocaleString('pt-BR')}</dd>
                </div>
            ))}
        </dl>
    </div>
);

// Componente Principal da Página
export default async function DashboardPage() {
  let metrics: Metrics | null = null;
  let error: string | null = null;

  try {
    metrics = await fetchMetrics();
  } catch (err) {
    console.error("Erro ao buscar métricas:", err);
    error = "Não foi possível carregar as métricas do servidor. Verifique o backend e o arquivo metrics.json.";
  }

  if (error) {
    return (
      <main className="container mx-auto p-4">
        <h1 className="text-2xl font-bold mb-6 text-red-600">Erro no Dashboard</h1>
        <p className="text-red-500">{error}</p>
      </main>
    );
  }

  if (!metrics) {
     return <div className="p-4 text-center">Carregando dados...</div>;
  }

  // Processamento dos dados no servidor (Server-Side)
  const ticketsByYear = aggregateByYear(metrics.tickets_by_day as DailyTicketCount[]);

  return (
    <main className="container mx-auto p-4 sm:p-6 lg:p-8">
      <h1 className="text-3xl font-bold mb-8 text-gray-500">Dashboard de Métricas</h1>
      
      {/* Cards de Métricas */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard title="Total Geral de Tickets" value={metrics.total_tickets.toLocaleString('pt-BR')} />
        <StatCard title="Total de Categorias" value={Object.keys(metrics.top_categories).length} />
        {/* Adicione mais um card simples aqui se necessário */}
        <StatCard title="Tickets no Último Ano" value={ticketsByYear[0]?.count.toLocaleString('pt-BR') || 'N/A'} />
      </div>

      {/* Top Listas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        {metrics.top_categories && (
          <TopItemsList title="Top 5 Categorias" data={metrics.top_categories} />
        )}
        {metrics.top_brands && (
          <TopItemsList title="Top 5 Marcas" data={metrics.top_brands} />
        )}
        {metrics.top_products && (
          <TopItemsList title="Top 5 Produtos" data={metrics.top_products} />
        )}
        <YearlyTicketsCard data={ticketsByYear} />
      </div>
    </main>
  );
}