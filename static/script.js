// Função para formatar valor monetário no padrão brasileiro (R$)
function formatarMoeda(valor) {
    if (typeof valor !== 'number' || isNaN(valor)) {
        return 'R$ 0,00';
    }
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(valor);
}

// Dados de exemplo (substitua com seus dados reais conforme necessário)
const dadosVendas = [
    { nome: 'Anderson', segunda: 52894.08, terca: 18245.38, quarta: 53967.95, quinta: 18553.33, sexta: 0 },
    { nome: 'Vitoria', segunda: 89715.38, terca: 31844.79, quarta: 0, quinta: 0, sexta: 0 },
    { nome: 'Jemima', segunda: 0, terca: 11597.24, quarta: 28200.08, quinta: 0, sexta: 0 },
    { nome: 'Maiany', segunda: 18629.33, terca: 23459.00, quarta: 17023.23, quinta: 0, sexta: 0 },
    { nome: 'Fernanda', segunda: 0, terca: 0, quarta: 0, quinta: 0, sexta: 0 },
    { nome: 'Nadia', segunda: 46888.05, terca: 31758.48, quarta: 69249.82, quinta: 0, sexta: 0 },
    { nome: 'Giovana', segunda: 16270.00, terca: 70779.45, quarta: 0, quinta: 0, sexta: 0 }
];

// Função principal para preencher a tabela com os dados formatados
function preencherTabela() {
    const tbody = document.querySelector('tbody');
    const tfoot = document.querySelector('tfoot');

    if (!tbody || !tfoot) {
        console.error('Elementos tbody ou tfoot não encontrados no HTML.');
        return;
    }

    // Limpa o conteúdo atual
    tbody.innerHTML = '';
    tfoot.innerHTML = '';

    // Dias da semana (ordem fixa)
    const diasSemana = ['segunda', 'terca', 'quarta', 'quinta', 'sexta'];
    const nomesDias = ['SEGUNDA', 'TERÇA', 'QUARTA', 'QUINTA', 'SEXTA'];

    // Objeto para acumular totais diários
    const totaisDiarios = {
        segunda: 0,
        terca: 0,
        quarta: 0,
        quinta: 0,
        sexta: 0
    };

    // Preenche cada linha de vendedor
    dadosVendas.forEach(vendedor => {
        const tr = document.createElement('tr');

        // Nome do vendedor
        const tdNome = document.createElement('td');
        tdNome.textContent = vendedor.nome;
        tdNome.style.fontWeight = 'bold';
        tdNome.style.color = '#FFD700'; // Amarelo dourado
        tr.appendChild(tdNome);

        // Valores por dia
        let totalVendedor = 0;
        diasSemana.forEach(dia => {
            const valor = vendedor[dia] || 0;
            totalVendedor += valor;
            totaisDiarios[dia] += valor;

            const td = document.createElement('td');
            td.textContent = formatarMoeda(valor);
            td.style.textAlign = 'right';
            tr.appendChild(td);
        });

        // Total do vendedor
        const tdTotal = document.createElement('td');
        tdTotal.textContent = formatarMoeda(totalVendedor);
        tdTotal.style.fontWeight = 'bold';
        tdTotal.style.color = '#FFD700';
        tdTotal.style.borderLeft = '2px solid #FFD700';
        tr.appendChild(tdTotal);

        tbody.appendChild(tr);
    });

    // Linha de TOTAL DIÁRIO no tfoot
    const trTotal = document.createElement('tr');

    const tdTituloTotal = document.createElement('td');
    tdTituloTotal.textContent = 'TOTAL DIÁRIO';
    tdTituloTotal.style.fontWeight = 'bold';
    tdTituloTotal.style.color = '#FFD700';
    trTotal.appendChild(tdTituloTotal);

    // Totais por dia
    let totalGeral = 0;
    diasSemana.forEach(dia => {
        const valor = totaisDiarios[dia];
        totalGeral += valor;
        const td = document.createElement('td');
        td.textContent = formatarMoeda(valor);
        td.style.textAlign = 'right';
        td.style.fontWeight = 'bold';
        td.style.color = '#FFD700';
        trTotal.appendChild(td);
    });

    // Total geral da semana
    const tdTotalGeral = document.createElement('td');
    tdTotalGeral.textContent = formatarMoeda(totalGeral);
    tdTotalGeral.style.fontWeight = 'bold';
    tdTotalGeral.style.color = '#FFD700';
    tdTotalGeral.style.borderLeft = '2px solid #FFD700';
    trTotal.appendChild(tdTotalGeral);

    tfoot.appendChild(trTotal);
}

// Inicializa a tabela quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    preencherTabela();
});