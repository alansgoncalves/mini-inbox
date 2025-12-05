// /frontend/app/tickets/page.tsx

import { fetchTickets } from "@/lib/services";
import { TicketsTable } from "@/components/TicketsTable";
import { Suspense } from "react";
import { Ticket } from "@/lib/types";

// Componente de página principal (Server Component)
export default async function TicketsPage() {
    let initialTickets: Ticket[] = [];
    let error: string | null = null;

    try {
        // Busca inicial de todos os tickets no servidor (SSR)
        initialTickets = await fetchTickets();
    } catch (err) {
        console.error("Erro ao carregar tickets iniciais:", err);
        error = "Não foi possível carregar a lista de tickets. Verifique o backend.";
    }

    return (
        <main className="container mx-auto p-4 sm:p-6 lg:p-8">
            <h1 className="text-3xl font-bold mb-8 text-gray-900">Tickets Mini Inbox</h1>
            
            {error ? (
                <div className="text-center p-8 bg-red-100 text-red-700 rounded-lg">
                    <p>{error}</p>
                </div>
            ) : (
                <Suspense fallback={<div className="text-center">Preparando a tabela...</div>}>
                    {/* Passa a lista inicial para o componente cliente */}
                    <TicketsTable initialTickets={initialTickets} />
                </Suspense>
            )}
        </main>
    );
}