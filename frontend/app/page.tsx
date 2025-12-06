import { redirect } from 'next/navigation';
//  * Renderiza usuário para /dashboard
export default function RootPage() {
  redirect('/dashboard');
}