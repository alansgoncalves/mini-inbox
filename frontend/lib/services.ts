import { api } from "./api";
import { Metrics } from "./types";
import { Ticket } from "./types";

// Função para buscar as métricas do backend
export async function fetchMetrics(): Promise<Metrics> {
  return api.get<Metrics>("/metrics");
}

// Função para buscar tickets, aceitando um termo de busca
export async function fetchTickets(searchTerm: string = ""): Promise<Ticket[]> {
  // api.get montará a URL como /tickets?search=searchTerm
  return api.get<Ticket[]>("/tickets", { query: { search: searchTerm } });
}

// Função para o para atulizar umm ticket 
export async function updateTicket(id: number, data: { status?: 'open' | 'closed' | 'pending', priority?: 'low' | 'medium' | 'high' }) {
    return api.patch(`/tickets/${id}`, data);
}

// Função para buscar um único ticket por ID no frontend
export async function fetchTicketDetails(id: number): Promise<Ticket | null> {
    // Busca todos os tickets 
    const allTickets = await api.get<Ticket[]>("/tickets"); 
    // Filtra para encontrar o ticket com o ID correspondente
    const ticket = allTickets.find(t => t.id === id);

    return ticket || null;
}