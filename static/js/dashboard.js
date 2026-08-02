document.addEventListener('DOMContentLoaded', () => {
  const state = {
    summary: null,
    profile: null,
    transactions: [],
    spending: null,
    insights: []
  };

  const renderSummaryCards = () => {
    if (!state.summary) return;
    const summary = state.summary;
    document.querySelector('[data-card="income"] .amount').textContent = `₹${summary.income.total.toLocaleString()}`;
    document.querySelector('[data-card="income"] .change').innerHTML = `${summary.income.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.income.change)}% vs last month`;

    document.querySelector('[data-card="expenses"] .amount').textContent = `₹${summary.expenses.total.toLocaleString()}`;
    document.querySelector('[data-card="expenses"] .change').innerHTML = `${summary.expenses.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.expenses.change)}% vs last month`;

    document.querySelector('[data-card="savings"] .amount').textContent = `₹${summary.savings.total.toLocaleString()}`;
    document.querySelector('[data-card="savings"] .change').innerHTML = `${summary.savings.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.savings.change)}% vs last month`;

    document.querySelector('[data-card="investments"] .amount').textContent = `₹${summary.investments.total.toLocaleString()}`;
    document.querySelector('[data-card="investments"] .change').innerHTML = `${summary.investments.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.investments.change)}% vs last month`;

    const totalValue = summary.income.total + summary.expenses.total + summary.savings.total + summary.investments.total;
    const totalValueNode = document.querySelector('[data-total-value]');
    if (totalValueNode) {
      totalValueNode.textContent = `₹${totalValue.toLocaleString()}`;
    }

    const legend = document.querySelector('.legend-list');
    if (!legend) return;
    legend.innerHTML = '';
    const segments = [
      { label: 'Income', amount: summary.income.total, percent: summary.chart_segments.income, color: '#2563EB' },
      { label: 'Expenses', amount: summary.expenses.total, percent: summary.chart_segments.expenses, color: '#F97316' },
      { label: 'Savings', amount: summary.savings.total, percent: summary.chart_segments.savings, color: '#10B981' },
      { label: 'Investments', amount: summary.investments.total, percent: summary.chart_segments.investments, color: '#8B5CF6' }
    ];

    segments.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'legend-row';
      row.innerHTML = `
        <div class="legend-label"><span class="legend-dot" style="background:${item.color}"></span>${item.label}</div>
        <div class="legend-meta"><strong>₹${item.amount.toLocaleString()}</strong><span>${item.percent}%</span></div>
      `;
      legend.appendChild(row);
    });
  };

  const renderProfile = () => {
    if (!state.profile) return;
    document.querySelector('[data-profile-name]').textContent = state.profile.name;
    document.querySelector('[data-profile-role]').textContent = state.profile.role;
    document.querySelector('[data-profile-email]').textContent = state.profile.email;
    document.querySelector('[data-profile-member]').textContent = state.profile.member_since;
    document.querySelector('[data-profile-status]').textContent = state.profile.account_status;
    document.querySelector('[data-health-score]').textContent = `${state.profile.financial_health_score}/100`;
  };

  const renderTransactions = () => {
    const list = document.querySelector('.transaction-list');
    if (!list) return;
    list.innerHTML = '';

    state.transactions.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'transaction-row';
      const iconClass = item.type === 'income' ? 'green' : item.type === 'investment' ? 'purple' : 'orange';
      const sign = item.type === 'income' ? '+' : '-';
      row.innerHTML = `
        <div class="transaction-left">
          <div class="transaction-icon ${iconClass}">${item.type === 'income' ? '💰' : item.type === 'investment' ? '📈' : '🛒'}</div>
          <div>
            <div class="transaction-title">${item.title}</div>
            <div class="transaction-subtitle">${item.category}</div>
          </div>
        </div>
        <div class="transaction-right">
          <div class="amount ${item.type === 'income' ? 'positive' : 'negative'}">${sign}₹${item.amount.toLocaleString()}</div>
          <div class="date">${item.date}</div>
        </div>
      `;
      list.appendChild(row);
    });
  };

  const renderAnalyticsChart = () => {
    if (!state.summary) return;
    const ctx = document.getElementById('analyticsChart');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Income', 'Expenses', 'Savings', 'Investments'],
        datasets: [{
          data: [state.summary.chart_segments.income, state.summary.chart_segments.expenses, state.summary.chart_segments.savings, state.summary.chart_segments.investments],
          backgroundColor: ['#2563EB', '#F97316', '#10B981', '#8B5CF6'],
          borderWidth: 0,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        cutout: '68%',
        plugins: {
          legend: { display: false },
          tooltip: { enabled: true }
        }
      },
      plugins: [{
        id: 'centerText',
        beforeDraw(chart) {
          const {ctx, chartArea} = chart;
          if (!chartArea) return;
          const totalValue = state.summary.income.total + state.summary.expenses.total + state.summary.savings.total + state.summary.investments.total;
          ctx.save();
          ctx.font = '600 14px Inter';
          ctx.fillStyle = '#64748B';
          ctx.textAlign = 'center';
          ctx.fillText('Total', chartArea.left + (chartArea.right - chartArea.left) / 2, chartArea.top + (chartArea.bottom - chartArea.top) / 2 - 8);
          ctx.font = '700 20px Inter';
          ctx.fillStyle = '#0F172A';
          ctx.fillText(`₹${totalValue.toLocaleString()}`, chartArea.left + (chartArea.right - chartArea.left) / 2, chartArea.top + (chartArea.bottom - chartArea.top) / 2 + 18);
          ctx.restore();
        }
      }]
    });
  };

  const renderSpendingChart = () => {
    if (!state.spending) return;
    const ctx = document.getElementById('spendingChart');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: state.spending.labels,
        datasets: [{
          label: 'Spending',
          data: state.spending.values,
          borderColor: '#3B82F6',
          backgroundColor: (context) => {
            const chart = context.chart;
            const {ctx, chartArea} = chart;
            if (!chartArea) return null;
            const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            gradient.addColorStop(0, 'rgba(59, 130, 246, 0.28)');
            gradient.addColorStop(1, 'rgba(59, 130, 246, 0.02)');
            return gradient;
          },
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 5,
          pointBackgroundColor: '#2563EB'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (value) => `₹${value / 1000}k` },
            grid: { color: 'rgba(148, 163, 184, 0.16)' }
          },
          x: { grid: { display: false } }
        }
      }
    });
  };

  const renderInsights = () => {
    const list = document.querySelector('.insight-list');
    if (!list) return;
    list.innerHTML = '';
    state.insights.forEach((item) => {
      const row = document.createElement('div');
      row.className = 'insight-item';
      row.innerHTML = `
        <div class="insight-row">
          <div class="insight-left">
            <div class="insight-icon" style="background:${item.color}1A;color:${item.color}">📊</div>
            <div>
              <div class="insight-title">${item.title}</div>
              <div class="insight-desc">${item.description}</div>
            </div>
          </div>
          <div class="insight-badge ${item.title === 'Budget Status' || item.title === 'Savings Rate' ? 'badge-on-track' : 'badge-purple'}">${item.status}</div>
        </div>
        <div class="progress-bar">
          <span style="background:${item.color};width:${item.percentage}%"></span>
        </div>
      `;
      list.appendChild(row);
    });
  };

  const fetchJson = async (url) => {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return response.json();
  };

  const bootstrapDashboard = async () => {
    try {
      const [summary, profile, transactions, spending, insights] = await Promise.all([
        fetchJson('/api/dashboard-summary'),
        fetchJson('/api/user-profile'),
        fetchJson('/api/recent-transactions'),
        fetchJson('/api/monthly-spending'),
        fetchJson('/api/insights')
      ]);
      state.summary = summary;
      state.profile = profile;
      state.transactions = transactions;
      state.spending = spending;
      state.insights = insights;
      renderSummaryCards();
      renderProfile();
      renderTransactions();
      renderAnalyticsChart();
      renderSpendingChart();
      renderInsights();
    } catch (error) {
      console.error(error);
    }
  };

  bootstrapDashboard();

  // Highlight the active sidebar nav item when clicked
  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach((nav) => nav.classList.remove('active'));
      item.classList.add('active');
    });
  });

  // NOTE: The old data-route event.preventDefault() block has been removed.
  // Previously it was intercepting all anchor link clicks and blocking navigation.
  // All buttons and links now navigate directly to their href URLs as expected.
});
