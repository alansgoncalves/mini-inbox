'use client';

import { useState } from 'react';
import { Ticket } from "@/lib/types";
import { updateTicket } from "@/lib/services"; 
import { useRouter } from 'next/navigation';

interface TicketDetailFormProps {
  initialTicket: Ticket;
}

const STATUS_OPTIONS = ['open', 'pending', 'closed'];
const PRIORITY_OPTIONS = ['low', 'medium', 'high'];

export function TicketDetailForm({ initialTicket }: TicketDetailFormProps) {
  const [status, setStatus] = useState(initialTicket.status);
  const [priority, setPriority] = useState(initialTicket.priority);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ text: string, type: 'success' | 'error' } | null>(null);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage(null);

    const dataToUpdate = {
        status: status !== initialTicket.status ? status : undefined,
        priority: priority !== initialTicket.priority ? priority : undefined,
    };

    if (dataToUpdate.status === undefined && dataToUpdate.priority === undefined) {
        setMessage({ text: 'Nenhuma alteração detectada para enviar.', type: 'error' });
        setIsLoading(false);
        return;
    }

    try {
        await updateTicket(initialTicket.id, dataToUpdate);
        
        // Simulação de sucesso e recarga de dados
        setMessage({ text: 'Ticket atualizado com sucesso!', type: 'success' });
        // Recarrega a página para atualizar os dados
        router.refresh(); 

    } catch (err) {
        setMessage({ text: 'Falha ao atualizar o ticket. Verifique o backend.', type: 'error' });
        console.error(err);
    } finally {
        setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="mt-8 space-y-6">
      <h2 className="text-xl font-semibold border-b pb-2 text-gray-800">Ações do Ticket</h2>

      {message && (
        <div className={`p-3 rounded-md ${message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {message.text}
        </div>
      )}

      {/* Seção Status */}
      <div>
        <label htmlFor="status" className="block text-sm font-semibold text-gray-700">Status Atual</label>
        <select
          id="status"
          value={status}
          onChange={(e) => setStatus(e.target.value as Ticket['status'])}
          className="block px-3 py-2.5 bg-white border border-blue-500 text-gray-800 text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 shadow-sm placeholder:text-gray-600"
        >
          {STATUS_OPTIONS.map(opt => (
            <option key={opt} value={opt} className='capitalize'>{opt}</option>
          ))}
        </select>
      </div>

      {/* Seção Prioridade */}
      <div>
        <label htmlFor="priority" className="block text-sm font-semibold text-gray-700">Prioridade</label>
        <select
          id="priority"
          value={priority}
          onChange={(e) => setPriority(e.target.value as Ticket['priority'])}
          className="block px-3 py-2.5 bg-white border border-blue-500 text-gray-800 text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 shadow-sm placeholder:text-gray-600"
        >
          {PRIORITY_OPTIONS.map(opt => (
            <option key={opt} value={opt} className='capitalize'>{opt}</option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {isLoading ? 'Salvando...' : 'Salvar Alterações'}
      </button>
    </form>
  );
}