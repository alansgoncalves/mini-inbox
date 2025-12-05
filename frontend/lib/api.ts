// Variável de ambiente se disponível, senão usa localhost como fallback
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

/**
 * Função para montar a URL com parâmetros de busca simples.
 * Exemplo: buildUrl("/tickets", {search: "problema"}) 
 *  "http://127.0.0.1:8000/tickets?search=Alan"
 */
function buildUrl(path: string, query?: Record<string, string>): string {
  // Cria um objeto URL completo combinando base + path
  const url = new URL(API_BASE_URL + path);
  // Se há parâmetros de query, adiciona à URL
  if (query) {
    // Itera sobre cada par chave-valor do objeto query
    for (const [key, value] of Object.entries(query)) {
      // Só adiciona se o valor não for undefined ou null
      if (value !== undefined && value !== null) {
        // .searchParams.set() adiciona o parâmetro na query string
        // Ex: url.searchParams.set("search", "Alan")
        url.searchParams.set(key, value);
      }
    }
  }
  // Retorna a URL completa como string
  // Ex: "http://127.0.0.1:8000/tickets?search=Alan"
  return url.toString();
}

// Função que todas as chamadas HTTP ao backend FastAPI
export const api = {
  // GET: Usado para /metrics e /tickets (listagem e busca)
  async get<T>(path: string, query?: Record<string, string>): Promise<T> {
    // Monta a URL completa com query params
    const url = buildUrl(path, query);
    // Faz a requisição GET usando fetch nativo
    const response = await fetch(url, {
      method: "GET",
      headers: {
        // Informa que esperamos receber JSON
        "Accept": "application/json",
      },
      // Cache desativado para garantir que os dados sejam sempre atualizados
      cache: "no-store" 
    });

    // Verifica se a resposta foi bem-sucedida (status 200)
    if (!response.ok) {
      // Trata erros e extrai mensagem de erro do JSON da resposta
      const errorData = await response.json().catch(() => response.statusText);
      // Lança erro com informações detalhadas
      throw new Error(`GET ${path} failed with status ${response.status}: ${JSON.stringify(errorData)}`);
    }
    // Retorna os valores do ticket
    return response.json() as Promise<T>;
  },

  // PATCH: Usado para atualizar status e priority do ticket
  async patch<T>(path: string, data: unknown): Promise<T> {
    // Faz a requisição PATCH usando fetch nativo
    const response = await fetch(API_BASE_URL + path, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      // Converte o objeto JavaScript para string JSON
      body: JSON.stringify(data),
    });

    // Verifica se a requisição foi bem-sucedida
    if (!response.ok) {
      // Trata erros e extrai mensagem de erro do JSON da resposta
      const errorData = await response.json().catch(() => response.statusText);
      // Lança erro com informações detalhadas
      throw new Error(`PATCH ${path} failed with status ${response.status}: ${JSON.stringify(errorData)}`);
    }
    // Retorna o recurso atualizado do ticket com os novos valores
    return response.json() as Promise<T>;
  },
};
