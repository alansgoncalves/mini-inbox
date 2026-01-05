import { fetchTicketDetails } from "@/lib/services";
import { Ticket } from "@/lib/types";
import { TicketDetailForm } from "@/components/TicketDetailForm";
import Link from 'next/link'

interface TicketPageProps {
  params: {
    id: string;
  };
}

// Define as opções para o formato DD/MM/YYYY
const dateOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
};



export default async function TicketPage({ params }: TicketPageProps) {

  const { id } = await params; 

  const idValue = String(id);
  const ticketId = parseInt(idValue);

  let ticket: Ticket | null = null;
  let error: string | null = null;

  if (isNaN(ticketId)) {
    error = "ID do ticket inválido.";
  } else {
    try {
      // Busca os detalhes do ticket no servidor
      ticket = await fetchTicketDetails(ticketId);
    } catch (err) {
      console.error("Erro ao buscar ticket:", err);
      error = "Não foi possível carregar os detalhes do ticket.";
    }
  }

  if (error || !ticket) {
    return (
      <main className="container mx-auto p-8">
        <h1 className="text-2xl font-bold mb-4 text-red-600">Erro ou Ticket Não Encontrado</h1>
        <p>{error || `O ticket com ID ${params.id} não foi encontrado.`}</p>
        <p className="mt-4 text-indigo-600 hover:underline"><Link href="/tickets">Voltar para a listL</Link></p>
      </main>
    );
  }

  return (
    <main className="container mx-auto p-4 sm:p-6 lg:p-8">
      
      <div className="flex justify-between items-start mb-8 flex-col sm:flex-row sm:items-center">
      <h1 className="text-3xl font-bold mb-6 text-gray-500">Ticket #{ticket.id}: {ticket.subject}</h1>

      <Link href="/tickets" passHref>
        <button className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg shadow-md transition duration-150 cursor-pointer">
          Voltar para lista de Tickets
        </button>
      </Link>
      </div>
      <div className="bg-white p-6 rounded-lg shadow-xl">
        <div className="grid grid-cols-2 gap-4 mb-6 text-gray-700">
          <p><strong>Cliente:</strong> {ticket.customer_name}</p>
          <p><strong>Canal:</strong> {ticket.channel}</p>
          <p><strong>Data de Criação:</strong> {new Date(ticket.created_at).toLocaleString('pt-BR', dateOptions)}</p>
        </div>

        {/* Componente Cliente para a Interação */}
        <TicketDetailForm initialTicket={ticket} /> 
      </div>
    </main>
  );
}