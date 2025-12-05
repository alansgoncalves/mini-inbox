'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { Ticket } from "@/lib/types";
import { fetchTickets } from "@/lib/services";

interface TicketsTableProps {
    initialTickets: Ticket[];
}

export function TicketsTable({ initialTickets }: TicketsTableProps) {
    const [tickets, setTickets] = useState(initialTickets);
    const [searchTerm, setSearchTerm] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Função que busca tickets
    const loadTickets = useCallback(async (term: string) => {
        setIsLoading(true);
        setError(null);
        try {
            const newTickets = await fetchTickets(term);
            setTickets(newTickets);
        } catch (err) {
            console.error(err);
            setError("Falha ao carregar tickets. Verifique a conexão com o backend.");
        } finally {
            setIsLoading(false);
        }
    }, []);

    const isInitialMount = useRef(true);

    // Efeito para carregar tickets quando o termo de busca muda
useEffect(() => {
        // Verifica se é a primeira montagem do componente
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return; // Sai sem buscar
        }
        // Se o termo de busca não estiver vazio, a busca é feita
        if (searchTerm.length > 0) {
            loadTickets(searchTerm);
        } 

    }, [searchTerm, loadTickets]);

    // Estilo básico para status
    const getStatusStyle = (status: Ticket['status']) => {
        switch (status) {
            case 'open': return 'bg-green-100 text-green-800';
            case 'closed': return 'bg-gray-100 text-gray-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-blue-100 text-blue-800';
        }
    };

    return (
        <div className="p-4 bg-white rounded-lg shadow-md">
            <div className="mb-4 flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-800">Tickets Recebidos</h2>
                <input
                    type="text"
                    placeholder="Buscar por assunto ou cliente..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="p-2 border border-gray-300 rounded-lg w-1/3"
                />
            </div>
            
            {isLoading && <p className="text-center text-indigo-600">Carregando tickets...</p>}
            {error && <p className="text-center text-red-500">{error}</p>}
            
            {!isLoading && !error && (
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assunto</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Cliente</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Prioridade</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {tickets.map((ticket) => (
                                <tr key={ticket.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{ticket.id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{ticket.subject}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">{ticket.customer_name}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusStyle(ticket.status)}`}>
                                            {ticket.status.toUpperCase()}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 capitalize">{ticket.priority}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <Link href={`/tickets/${ticket.id}`} className="text-indigo-600 hover:text-indigo-900">
                                            Detalhes
                                        </Link>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {tickets.length === 0 && !isLoading && !error && (
                <p className="text-center text-gray-500 mt-4">Nenhum ticket encontrado.</p>
            )}
        </div>
    );
}