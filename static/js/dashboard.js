document.addEventListener('DOMContentLoaded', () => {
  const state = {
    summary: null,
    profile: null,
    transactions: [],
    spending: null,
    insights: []
  };

  let analyticsChartInstance = null;
  let spendingChartInstance = null;
  let isRefreshing = false;

  const safeSetText = (selector, text) => {
    const el = document.querySelector(selector);
    if (el) el.textContent = text;
  };

  const safeSetHtml = (selector, html) => {
    const el = document.querySelector(selector);
    if (el) el.innerHTML = html;
  };

  const renderSummaryCards = () => {
    if (!state.summary) return;
    const summary = state.summary;

    safeSetText('[data-card="income"] .amount', `₹${summary.income.total.toLocaleString()}`);
    safeSetHtml('[data-card="income"] .change', `${summary.income.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.income.change)}% vs last month`);

    safeSetText('[data-card="expenses"] .amount', `₹${summary.expenses.total.toLocaleString()}`);
    safeSetHtml('[data-card="expenses"] .change', `${summary.expenses.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.expenses.change)}% vs last month`);

    safeSetText('[data-card="savings"] .amount', `₹${summary.savings.total.toLocaleString()}`);
    safeSetHtml('[data-card="savings"] .change', `${summary.savings.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.savings.change)}% vs last month`);

    safeSetText('[data-card="investments"] .amount', `₹${summary.investments.total.toLocaleString()}`);
    safeSetHtml('[data-card="investments"] .change', `${summary.investments.change >= 0 ? '↑' : '↓'} ${Math.abs(summary.investments.change)}% vs last month`);

    const legend = document.querySelector('.legend-list');
    if (legend) {
      legend.innerHTML = '';
      const segments = [
        { label: 'Expenses', amount: summary.expenses.total, percent: summary.chart_segments.expenses, color: '#2563EB' },
        { label: 'Savings', amount: summary.savings.total, percent: summary.chart_segments.savings, color: '#10B981' },
        { label: 'Investments', amount: summary.investments.total, percent: summary.chart_segments.investments, color: '#F97316' },
        { label: 'Remaining', amount: summary.remaining.total, percent: summary.chart_segments.remaining, color: '#8B5CF6' }
      ];

      const icons = {
        'Expenses': '<i class="bi bi-wallet2" style="font-size:1.15rem;"></i>',
        'Savings': '<i class="bi bi-piggy-bank" style="font-size:1.15rem;"></i>',
        'Investments': '<i class="bi bi-graph-up-arrow" style="font-size:1.15rem;"></i>',
        'Remaining': '<i class="bi bi-arrow-repeat" style="font-size:1.15rem;"></i>'
      };

      segments.forEach((item) => {
        const row = document.createElement('div');
        row.className = 'legend-row';
        row.style.borderTop = `3px solid ${item.color}`;
        row.innerHTML = `
          <div class="legend-label" style="color:${item.color}">${icons[item.label] || ''} <span>${item.label}</span></div>
          <div class="legend-meta"><strong>₹${item.amount.toLocaleString()}</strong> <span style="font-size:0.78rem;font-weight:600;color:#64748B;">(${item.percent}%)</span></div>
        `;
        legend.appendChild(row);
      });
    }

    safeSetText('#income-allocation-subtitle', `How your ₹${summary.income.total.toLocaleString()} income is allocated`);

    if (summary.savings.total > 0) {
      safeSetText('#savings-diff-text', `You saved ₹${summary.savings.total.toLocaleString()} this month`);
    } else {
      safeSetText('#savings-diff-text', `Live financial breakdown from your transactions`);
    }
  };

  const renderProfile = () => {
    if (!state.profile) return;
    safeSetText('[data-profile-name]', state.profile.name);
    safeSetText('[data-profile-role]', state.profile.role);
    safeSetText('[data-profile-email]', state.profile.email);
    safeSetText('[data-profile-member]', state.profile.member_since);
    safeSetText('[data-profile-status]', state.profile.account_status);
    safeSetText('[data-health-score]', `${state.profile.financial_health_score}/100`);
  };

  const renderTransactions = () => {
    const list = document.querySelector('.transaction-list');
    if (!list) return;
    list.innerHTML = '';

    if (!state.transactions || state.transactions.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:24px 0;color:#94A3B8;font-size:0.88rem;">No recent transactions found</div>';
      return;
    }

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

    if (analyticsChartInstance) {
      analyticsChartInstance.destroy();
    }

    analyticsChartInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Expenses', 'Savings', 'Investments', 'Remaining'],
        datasets: [{
          data: [
            state.summary.chart_segments.expenses || 0,
            state.summary.chart_segments.savings || 0,
            state.summary.chart_segments.investments || 0,
            state.summary.chart_segments.remaining || 0
          ],
          backgroundColor: ['#2563EB', '#10B981', '#F97316', '#8B5CF6'],
          borderWidth: 0,
          hoverOffset: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
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
          const totalValue = state.summary.income.total;
          ctx.save();
          ctx.font = '600 13px Inter';
          ctx.fillStyle = '#64748B';
          ctx.textAlign = 'center';
          ctx.fillText('Total Income', chartArea.left + (chartArea.right - chartArea.left) / 2, chartArea.top + (chartArea.bottom - chartArea.top) / 2 - 8);
          ctx.font = '700 20px Inter';
          ctx.fillStyle = '#0F172A';
          ctx.fillText(`₹${totalValue.toLocaleString()}`, chartArea.left + (chartArea.right - chartArea.left) / 2, chartArea.top + (chartArea.bottom - chartArea.top) / 2 + 16);
          ctx.restore();
        }
      }]
    });
  };

  const renderSpendingChart = () => {
    if (!state.spending) return;
    const ctx = document.getElementById('spendingChart');
    if (!ctx) return;

    if (spendingChartInstance) {
      spendingChartInstance.destroy();
    }

    const values = state.spending.values || [0];
    const peak = Math.max(...values, 0);
    safeSetText('#spending-peak-tooltip', `Peak: ₹${peak.toLocaleString()}`);

    spendingChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: state.spending.labels || ['No Data'],
        datasets: [{
          label: 'Spending',
          data: values,
          borderColor: '#3B82F6',
          borderWidth: 3,
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
          pointRadius: 5,
          pointHoverRadius: 7,
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
            ticks: {
              callback: (value) => {
                if (value >= 1000) return `₹${Math.round(value / 1000)}k`;
                return `₹${value}`;
              }
            },
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

    if (!state.insights || state.insights.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:24px 0;color:#94A3B8;font-size:0.88rem;">No insights available</div>';
      return;
    }

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
          <span style="background:${item.color};width:${Math.min(100, Math.max(0, item.percentage))}%"></span>
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

  const bootstrapDashboard = async (isRefresh = false) => {
    if (isRefreshing) return;
    isRefreshing = true;

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

      if (isRefresh) {
        // Flash success indicator on stat cards
        document.querySelectorAll('.stat-card').forEach(card => {
          card.classList.add('refresh-flash');
          setTimeout(() => card.classList.remove('refresh-flash'), 800);
        });
      }
    } catch (error) {
      console.error('Error bootstrapping dashboard:', error);
    } finally {
      isRefreshing = false;
    }
  };

  bootstrapDashboard(false);


  document.querySelectorAll('.nav-item').forEach((item) => {
    item.addEventListener('click', () => {
      document.querySelectorAll('.nav-item').forEach((nav) => nav.classList.remove('active'));
      item.classList.add('active');
    });
  });

  // Set dynamic greeting based on time of day
  (function initDashboardGreeting() {
    const greetingEl = document.getElementById('dashboard-greeting');
    const iconEl = document.getElementById('dashboard-greeting-icon');
    if (!greetingEl) return;

    const username = greetingEl.getAttribute('data-username') || 'User';
    const hour = new Date().getHours();
    let greet = 'Hello';
    let iconClass = 'bi-sun';

    if (hour < 12) {
      greet = 'Good morning';
      iconClass = 'bi-sun';
    } else if (hour < 17) {
      greet = 'Good afternoon';
      iconClass = 'bi-cloud-sun';
    } else {
      greet = 'Good evening';
      iconClass = 'bi-moon-stars';
    }

    greetingEl.textContent = `${greet}, ${username}!`;
    if (iconEl) {
      iconEl.className = `bi ${iconClass}`;
    }
  })();

  // Animate stat cards on load
  document.querySelectorAll('.stat-card').forEach((card, i) => {
    card.style.animationDelay = `${i * 80}ms`;
    card.classList.add('card-enter');
  });
});
