// GymOS AI Revenue Recovery Sentinel - Interactive Frontend Logic

let globalScenarios = [];
let chartRecovery = null;
let chartGmv = null;

document.addEventListener("DOMContentLoaded", async () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  await loadPresetScenarios();
  await refreshAuditTrail();
  initCharts();

  const nameInput = document.getElementById("input-name");
  if (nameInput) {
    nameInput.addEventListener("input", (e) => {
      syncWhatsAppMockup(e.target.value, document.getElementById("input-tier")?.value, document.getElementById("input-amount")?.value);
    });
  }

  const chatMemberSel = document.getElementById("chat-member-selector");
  if (chatMemberSel) {
    chatMemberSel.addEventListener("change", (e) => {
      onChatMemberChange(e.target.value);
    });
  }

  const resetBtn = document.getElementById("btn-reset-chat");
  if (resetBtn) {
    resetBtn.addEventListener("click", (e) => {
      e.preventDefault();
      resetWhatsAppConversation();
    });
  }
});

function switchTab(tabId) {
  document.querySelectorAll("main > section").forEach(el => el.classList.add("hidden"));
  document.getElementById(tabId).classList.remove("hidden");

  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.classList.remove("border-blue-500", "text-blue-400");
    btn.classList.add("border-transparent", "text-slate-400");
  });

  const activeBtn = document.getElementById("btn-" + tabId);
  if (activeBtn) {
    activeBtn.classList.remove("border-transparent", "text-slate-400");
    activeBtn.classList.add("border-blue-500", "text-blue-400");
  }

  if (tabId === "tab-chat") {
    syncWhatsAppMockup(
      document.getElementById("input-name")?.value,
      document.getElementById("input-tier")?.value,
      document.getElementById("input-amount")?.value
    );
  } else if (tabId === "tab-optimizer") {
    loadOptimizerRails();
  } else if (tabId === "tab-b2b") {
    loadB2BInvoices();
  } else if (tabId === "tab-audit") {
    refreshAuditTrail();
  }

  if (window.lucide) {
    lucide.createIcons();
  }
}

async function loadPresetScenarios() {
  try {
    const res = await fetch("/api/scenarios");
    const data = await res.json();
    globalScenarios = data.scenarios || [];

    const select1 = document.getElementById("scenario-selector");
    const select2 = document.getElementById("chat-member-selector");

    if (select1) select1.innerHTML = '<option value="">-- Load Sample Scenario --</option>';
    if (select2) select2.innerHTML = '<option value="">-- Select Member to Chat --</option>';

    globalScenarios.forEach((s, idx) => {
      const optText = `[${s.scenario_id}] ${s.name} (${s.membership_tier}) - ${s.last_failure_code}`;
      
      if (select1) {
        const opt1 = document.createElement("option");
        opt1.value = idx;
        opt1.innerText = optText;
        select1.appendChild(opt1);
      }

      if (select2) {
        const opt2 = document.createElement("option");
        opt2.value = idx;
        opt2.innerText = `👤 ${s.name} (₹${s.membership_amount.toLocaleString()}) · ${s.membership_tier}`;
        select2.appendChild(opt2);
      }
    });

    if (globalScenarios.length > 0) {
      selectScenarioFromDropdown(0);
    }
  } catch (err) {
    console.error("Failed to load scenarios", err);
  }
}

function selectScenarioFromDropdown(indexStr) {
  if (indexStr === "" || indexStr === undefined) return;
  const s = globalScenarios[parseInt(indexStr)];
  if (!s) return;

  document.getElementById("input-name").value = s.name;
  document.getElementById("input-phone").value = s.phone;
  document.getElementById("input-tier").value = s.membership_tier;
  document.getElementById("input-amount").value = s.membership_amount;
  document.getElementById("input-days-inactive").value = s.days_since_last_checkin;
  document.getElementById("input-visits").value = s.actual_visits_last_30_days;
  document.getElementById("input-failure-code").value = s.last_failure_code;
  document.getElementById("input-fails").value = s.consecutive_failed_attempts;
  document.getElementById("input-optout").checked = s.opted_out;

  const chatSel = document.getElementById("chat-member-selector");
  if (chatSel && chatSel.value !== indexStr) {
    chatSel.value = indexStr;
  }

  const mainSel = document.getElementById("scenario-selector");
  if (mainSel && mainSel.value !== indexStr) {
    mainSel.value = indexStr;
  }

  syncWhatsAppMockup(s.name, s.membership_tier, s.membership_amount);
}

function onChatMemberChange(indexStr) {
  if (indexStr === "" || indexStr === undefined) return;
  selectScenarioFromDropdown(indexStr);
  resetWhatsAppConversation();
}

function resetWhatsAppConversation() {
  const name = document.getElementById("input-name")?.value || "Rahul Sharma";
  const firstName = name.split(" ")[0];
  const amount = parseFloat(document.getElementById("input-amount")?.value) || 5849;
  const tier = document.getElementById("input-tier")?.value || "Quarterly Pro";
  const discountedAmt = Math.round(amount * 0.9);

  const container = document.getElementById("chat-messages-container");
  if (!container) return;

  container.innerHTML = `
    <!-- Initial AI Recovery Outreach Message -->
    <div class="flex justify-start">
      <div class="bg-[#202c33] text-slate-200 p-3.5 rounded-2xl rounded-tl-none max-w-md shadow-md space-y-2">
        <p id="chat-initial-greeting">Arre ${firstName} bhai! 💪 IronPeak Gym mein aapko miss kar rahe hain. Goals break nahi hone chahiye!</p>
        <p>Aapke active return ke liye humne exclusive renewal link ready kiya hai:</p>
        <div class="p-2.5 bg-[#111b21] rounded-xl border border-blue-500/30 text-cyan-300 font-mono text-[11px] flex justify-between items-center">
          <span id="chat-initial-link-text">👉 /checkout?id=plink_init&amount=${discountedAmt}</span>
          <a id="chat-initial-link-btn" href="/checkout?id=plink_init&amount=${discountedAmt}&name=${encodeURIComponent(name)}&tier=${encodeURIComponent(tier)}" target="_blank" class="px-2 py-0.5 rounded bg-blue-600 hover:bg-blue-500 text-white font-sans text-[10px]">Open Checkout</a>
        </div>
        <div class="text-[10px] text-slate-400 text-right">10:15 AM · ✓✓</div>
      </div>
    </div>
  `;

  syncWhatsAppMockup(name, tier, amount);
}

function syncWhatsAppMockup(name, tier, amount) {
  const safeName = name || "Rahul Sharma";
  const firstName = safeName.split(" ")[0];
  const safeTier = tier || "Quarterly Pro";
  const safeAmt = amount || 5849;
  const discountedAmt = Math.round(safeAmt * 0.9);
  
  const greetEl = document.getElementById("chat-initial-greeting");
  if (greetEl) {
    greetEl.innerText = `Arre ${firstName} bhai! 💪 IronPeak Gym mein aapko miss kar rahe hain. Goals break nahi hone chahiye!`;
  }
  const linkTextEl = document.getElementById("chat-initial-link-text");
  if (linkTextEl) {
    linkTextEl.innerText = `👉 /checkout?id=plink_init&amount=${discountedAmt}`;
  }
  const headerEl = document.getElementById("chat-header-member");
  if (headerEl) {
    headerEl.innerText = `Chat with ${safeName} · Official Verified Account`;
  }
  const linkBtn = document.getElementById("chat-initial-link-btn");
  if (linkBtn) {
    linkBtn.href = `/checkout?id=plink_init&amount=${discountedAmt}&name=${encodeURIComponent(safeName)}&tier=${encodeURIComponent(safeTier)}`;
  }
}

function loadRandomScenario() {
  if (globalScenarios.length === 0) return;
  const randIdx = Math.floor(Math.random() * globalScenarios.length);
  document.getElementById("scenario-selector").value = randIdx;
  selectScenarioFromDropdown(randIdx);
}

async function executeSingleRecovery() {
  const memberPayload = {
    member_id: "mem_custom_" + Date.now().toString().slice(-6),
    tenant_id: "gym_ironpeak_001",
    name: document.getElementById("input-name").value,
    phone: document.getElementById("input-phone").value,
    email: "member@example.com",
    language_preference: "hinglish",
    membership_tier: document.getElementById("input-tier").value,
    membership_amount: parseFloat(document.getElementById("input-amount").value),
    plan_start_date: "2026-06-01",
    plan_expiry_date: "2026-09-01",
    baseline_visits_per_week: 4.0,
    actual_visits_last_30_days: parseInt(document.getElementById("input-visits").value),
    days_since_last_checkin: parseInt(document.getElementById("input-days-inactive").value),
    lifetime_paid_inr: 15000.0,
    previous_payment_method: "UPI_AUTOPAY",
    consecutive_failed_attempts: parseInt(document.getElementById("input-fails").value),
    opted_out: document.getElementById("input-optout").checked,
    last_failure_code: document.getElementById("input-failure-code").value,
    last_failure_timestamp: new Date().toISOString(),
    historical_discount_given: 0.0
  };

  try {
    const res = await fetch("/api/recover/single", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(memberPayload)
    });
    const result = await res.json();

    // Render Outputs
    const formattedRootCause = (result.root_cause || "--").replace(/_/g, " ");
    const formattedStrategy = (result.strategy_applied || "--").replace(/_/g, " ");
    document.getElementById("output-root-cause").innerText = formattedRootCause;
    document.getElementById("output-strategy").innerText = `${formattedStrategy} (${result.discount_percentage}% off)`;
    document.getElementById("output-amount").innerText = `₹${result.discounted_amount.toLocaleString()}`;

    // Badge status
    const badge = document.getElementById("badge-status");
    badge.innerText = result.status;
    if (result.status === "DISPATCHED" || result.status === "SCHEDULED_RETRY") {
      badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
    } else if (result.status === "ESCALATED") {
      badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-400 border border-purple-500/30";
    } else {
      badge.className = "px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30";
    }

    // Guardrail notes
    document.getElementById("guardrail-badge").innerText = result.guardrail_passed ? "Passed Policy Check" : "Policy Enforced Block";
    document.getElementById("guardrail-badge").className = result.guardrail_passed ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold";
    
    const notesList = document.getElementById("guardrail-notes-list");
    notesList.innerHTML = "";
    (result.guardrail_reasons || []).forEach(n => {
      const li = document.createElement("li");
      li.innerText = n;
      notesList.appendChild(li);
    });

    // Razorpay dynamic link
    const rzpBox = document.getElementById("razorpay-link-container");
    if (result.razorpay_payment_link) {
      rzpBox.classList.remove("hidden");
      document.getElementById("output-rzp-url").value = result.razorpay_payment_link;
      document.getElementById("btn-open-rzp-link").href = result.razorpay_payment_link;
    } else {
      rzpBox.classList.add("hidden");
    }

    // Copy box
    document.getElementById("output-copy-box").innerText = result.recovery_copy || "No copy generated.";

    if (window.lucide) {
      lucide.createIcons();
    }
  } catch (err) {
    console.error("Recovery execution failed", err);
    alert("Recovery execution failed: " + err.message);
  }
}

async function runBatchSimulation() {
  const btn = document.getElementById("btn-run-benchmark");
  btn.innerHTML = `<span class="animate-spin inline-block mr-2">🔄</span> Processing 100 Scenarios...`;
  btn.disabled = true;

  try {
    const res = await fetch("/api/recover/batch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ seed: 42 })
    });
    const data = await res.json();

    // Update KPI Header Cards
    document.getElementById("kpi-rate").innerText = `${data.ai_recovery_rate_percent}%`;
    document.getElementById("kpi-gmv").innerText = `₹${data.ai_gross_recovered_gmv_inr.toLocaleString()}`;
    document.getElementById("kpi-roi").innerText = `${data.ai_net_roi_multiple}x`;
    document.getElementById("kpi-compliance").innerText = `${100 - data.policy_violations_count}%`;

    // Update Charts
    updateCharts(data);

    // Update Table
    const tbody = document.getElementById("benchmark-table-body");
    tbody.innerHTML = "";
    (data.scenario_details.slice(0, 20) || []).forEach(row => {
      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-900/40 transition";
      tr.innerHTML = `
        <td class="py-2.5 px-4 font-mono text-slate-400">${row.scenario_id}</td>
        <td class="py-2.5 px-4 font-medium text-white">${row.member_name}</td>
        <td class="py-2.5 px-4 font-mono">₹${row.amount.toLocaleString()}</td>
        <td class="py-2.5 px-4 text-cyan-400">${row.root_cause}</td>
        <td class="py-2.5 px-4 text-purple-400">${row.strategy}</td>
        <td class="py-2.5 px-4">${row.discount_percent}%</td>
        <td class="py-2.5 px-4"><span class="px-2 py-0.5 rounded text-[10px] bg-slate-800 border border-slate-700 font-semibold">${row.status}</span></td>
        <td class="py-2.5 px-4">${row.ai_recovered ? '<span class="text-emerald-400 font-bold">✓ Recovered</span>' : '<span class="text-slate-500">Unrecovered</span>'}</td>
      `;
      tbody.appendChild(tr);
    });

  } catch (err) {
    console.error("Batch simulation error", err);
    alert("Batch simulation error: " + err.message);
  } finally {
    btn.innerHTML = `<i data-lucide="play" class="w-4 h-4 mr-2"></i><span>Execute 100-Case Benchmark</span>`;
    btn.disabled = false;
    if (window.lucide) {
      lucide.createIcons();
    }
  }
}

function initCharts() {
  const ctxRecovery = document.getElementById("chartRecoveryRate").getContext("2d");
  chartRecovery = new Chart(ctxRecovery, {
    type: "bar",
    data: {
      labels: ["AI Recovery Agent", "Naive Baseline (No AI)"],
      datasets: [{
        label: "Recovery Rate (%)",
        data: [78.0, 18.0],
        backgroundColor: ["#3395ff", "#475569"],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, max: 100, grid: { color: "#1e293b" }, ticks: { color: "#94a3b8" } },
        x: { grid: { display: false }, ticks: { color: "#94a3b8" } }
      }
    }
  });

  const ctxGmv = document.getElementById("chartGmvLift").getContext("2d");
  chartGmv = new Chart(ctxGmv, {
    type: "bar",
    data: {
      labels: ["AI Recovered GMV", "Baseline GMV", "Incentive Spend", "Net AI Gain"],
      datasets: [{
        label: "Amount (INR)",
        data: [378500, 87000, 21200, 357300],
        backgroundColor: ["#10b981", "#64748b", "#f59e0b", "#8b5cf6"],
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "#1e293b" }, ticks: { color: "#94a3b8" } },
        x: { grid: { display: false }, ticks: { color: "#94a3b8" } }
      }
    }
  });
}

function updateCharts(data) {
  if (chartRecovery) {
    chartRecovery.data.datasets[0].data = [data.ai_recovery_rate_percent, data.baseline_recovery_rate_percent];
    chartRecovery.update();
  }
  if (chartGmv) {
    chartGmv.data.datasets[0].data = [
      data.ai_gross_recovered_gmv_inr,
      data.baseline_recovered_gmv_inr,
      data.ai_discount_incentive_cost_inr,
      data.ai_net_recovered_inr
    ];
    chartGmv.update();
  }
}

async function refreshAuditTrail() {
  try {
    const res = await fetch("/api/audit-trail?limit=15");
    const data = await res.json();
    const container = document.getElementById("audit-log-container");
    container.innerHTML = "";

    if (!data.entries || data.entries.length === 0) {
      container.innerHTML = '<div class="text-slate-500 text-center py-6">No audit records logged yet. Trigger a recovery to generate entries.</div>';
      return;
    }

    data.entries.forEach(entry => {
      const card = document.createElement("div");
      card.className = "p-3.5 bg-slate-900 rounded-xl border border-slate-800 space-y-1.5";
      card.innerHTML = `
        <div class="flex items-center justify-between text-[11px] text-slate-400">
          <span class="text-blue-400 font-bold font-mono">SHA-256: ${entry.entry_hash.slice(0, 16)}...</span>
          <span class="font-mono text-[10px] text-slate-400 font-semibold">${formatIST(entry.timestamp)}</span>
        </div>
        <div class="text-xs text-slate-200">
          <span class="text-purple-400 font-semibold">[${entry.member_id}]</span> Trigger: <span class="text-cyan-300">${entry.trigger_signal}</span> | Verdict: <span class="text-emerald-400 font-bold">${entry.guardrail_verdict}</span> | Status: <span class="text-slate-300 font-bold">${entry.outcome_status}</span>
        </div>
        <div class="text-[11px] text-slate-400">
          Root Cause: <span class="text-slate-300">${entry.diagnostics.root_cause}</span> (${Math.round((entry.diagnostics.confidence || 0.9)*100)}% conf)
        </div>
        <div class="text-[10px] text-slate-500 break-all">
          Prev Hash: ${entry.previous_hash.slice(0, 16)}...
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load audit trail", err);
  }
}

async function savePolicies() {
  const payload = {
    max_discount_percentage: parseFloat(document.getElementById("slider-discount").value),
    max_touches: parseInt(document.getElementById("slider-touches").value),
    strict_opt_out: document.getElementById("toggle-optout").checked,
    vip_threshold_inr: parseFloat(document.getElementById("slider-vip").value),
    razorpay_key_id: document.getElementById("input-rzp-key-id")?.value.trim(),
    razorpay_key_secret: document.getElementById("input-rzp-key-secret")?.value.trim()
  };

  try {
    const res = await fetch("/api/policies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    alert("Policy guardrails & Razorpay credentials successfully updated!");
  } catch (err) {
    alert("Failed to save policies: " + err.message);
  }
}

// ==========================================
// Two-Way WhatsApp Negotiation Simulator
// ==========================================

function sendQuickReply(text) {
  document.getElementById("chat-user-input").value = text;
  sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById("chat-user-input");
  const messageText = input.value.trim();
  if (!messageText) return;

  const container = document.getElementById("chat-messages-container");

  // Append User Bubble (Right)
  const userBubble = document.createElement("div");
  userBubble.className = "flex justify-end";
  userBubble.innerHTML = `
    <div class="bg-[#005c4b] text-slate-100 p-3 rounded-2xl rounded-tr-none max-w-md shadow-md space-y-1">
      <p>${escapeHtml(messageText)}</p>
      <div class="text-[10px] text-emerald-200 text-right">Just now · ✓✓</div>
    </div>
  `;
  container.appendChild(userBubble);
  input.value = "";
  container.scrollTop = container.scrollHeight;

  // Typing indicator
  const typingIndicator = document.createElement("div");
  typingIndicator.id = "typing-indicator";
  typingIndicator.className = "flex justify-start";
  typingIndicator.innerHTML = `
    <div class="bg-[#202c33] text-slate-400 p-3 rounded-2xl rounded-tl-none text-xs flex items-center space-x-2">
      <span class="animate-bounce">●</span><span class="animate-bounce delay-100">●</span><span class="animate-bounce delay-200">●</span>
      <span>AI Concierge thinking & checking policy rules...</span>
    </div>
  `;
  container.appendChild(typingIndicator);
  container.scrollTop = container.scrollHeight;

  // Current selected member profile
  const member = {
    member_id: "mem_blr_4091",
    name: document.getElementById("input-name").value || "Rahul Sharma",
    phone: document.getElementById("input-phone").value || "+919876543210",
    email: "rahul.sharma@example.com",
    language_preference: "hinglish",
    membership_tier: document.getElementById("input-tier").value || "QUARTERLY_PRO",
    membership_amount: parseFloat(document.getElementById("input-amount").value) || 6499.0,
    plan_start_date: "2026-06-01",
    plan_expiry_date: "2026-09-01",
    baseline_visits_per_week: 4.0,
    actual_visits_last_30_days: 2,
    days_since_last_checkin: 18,
    lifetime_paid_inr: 15000.0,
    previous_payment_method: "UPI_AUTOPAY",
    consecutive_failed_attempts: 1,
    opted_out: false,
    last_failure_code: "NONE"
  };

  try {
    const res = await fetch("/api/chat/respond", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ member, message: messageText })
    });
    const result = await res.json();

    typingIndicator.remove();

    // Append AI Response Bubble (Left)
    const aiBubble = document.createElement("div");
    aiBubble.className = "flex justify-start";
    
    let linkBlock = "";
    if (result.payment_link) {
      linkBlock = `
        <div class="p-2.5 bg-[#111b21] rounded-xl border border-emerald-500/30 text-emerald-300 font-mono text-[11px] flex justify-between items-center">
          <span>${result.payment_link}</span>
          <a href="${result.payment_link}" target="_blank" class="px-2 py-0.5 rounded bg-emerald-600 text-white font-sans text-[10px]">Open</a>
        </div>
      `;
    }

    aiBubble.innerHTML = `
      <div class="bg-[#202c33] text-slate-200 p-3.5 rounded-2xl rounded-tl-none max-w-md shadow-md space-y-2">
        <div class="text-[10px] text-cyan-400 font-mono font-bold flex items-center space-x-1">
          <span>⚡ Action: ${result.action_executed.action || result.intent}</span>
        </div>
        <p class="whitespace-pre-line">${escapeHtml(result.reply_message)}</p>
        ${linkBlock}
        <div class="text-[10px] text-slate-400 text-right font-mono">${formatIST(new Date())} · ✓✓</div>
      </div>
    `;
    container.appendChild(aiBubble);
    container.scrollTop = container.scrollHeight;

    // Refresh audit log
    await refreshAuditTrail();
  } catch (err) {
    typingIndicator.remove();
    console.error("Chat response error", err);
  }
}

function formatIST(isoOrDateStr) {
  if (!isoOrDateStr) return "";
  if (typeof isoOrDateStr === "string" && isoOrDateStr.includes("IST")) {
    return isoOrDateStr;
  }
  try {
    const d = new Date(isoOrDateStr);
    if (isNaN(d.getTime())) return String(isoOrDateStr);
    return d.toLocaleString("en-IN", {
      timeZone: "Asia/Kolkata",
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: true
    }) + " IST";
  } catch (e) {
    return String(isoOrDateStr);
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// ==========================================
// B2B Corporate Accounts Receivable (AR)
// ==========================================

let globalInvoices = [];

async function loadB2BInvoices() {
  try {
    const res = await fetch("/api/b2b/invoices");
    const data = await res.json();
    globalInvoices = data.invoices || [];

    const tbody = document.getElementById("b2b-invoices-tbody");
    tbody.innerHTML = "";

    globalInvoices.forEach((inv, idx) => {
      let badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/30";
      if (inv.days_overdue >= 60) badgeColor = "bg-rose-500/10 text-rose-400 border-rose-500/30";
      else if (inv.days_overdue >= 30) badgeColor = "bg-orange-500/10 text-orange-400 border-orange-500/30";

      const tr = document.createElement("tr");
      tr.className = "hover:bg-slate-900/40 transition";
      tr.innerHTML = `
        <td class="py-3 px-4 font-mono font-bold text-slate-300">${inv.invoice_id}</td>
        <td class="py-3 px-4 font-medium text-white">
          <div>${inv.company_name}</div>
          <div class="text-[10px] text-slate-400">${inv.contact_person}</div>
        </td>
        <td class="py-3 px-4 font-mono">${inv.employee_seat_count} seats</td>
        <td class="py-3 px-4 font-mono font-bold text-white">₹${inv.invoice_amount_inr.toLocaleString()}</td>
        <td class="py-3 px-4"><span class="font-mono text-rose-400 font-bold">${inv.days_overdue} days</span></td>
        <td class="py-3 px-4"><span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${badgeColor}">${inv.status}</span></td>
        <td class="py-3 px-4 text-right">
          <button onclick="triggerCorporateDunning(${idx})" class="px-3 py-1.5 rounded-lg bg-gradient-to-r from-amber-600 to-orange-500 hover:from-amber-500 hover:to-orange-400 text-white font-bold text-xs shadow-md transition">
            Trigger Dunning
          </button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Failed to load B2B invoices", err);
  }
}

async function triggerCorporateDunning(index) {
  const invoice = globalInvoices[index];
  if (!invoice) return;

  try {
    const res = await fetch("/api/b2b/dunning", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ invoice })
    });
    const result = await res.json();

    const box = document.getElementById("b2b-output-container");
    box.classList.remove("hidden");
    document.getElementById("b2b-dunning-stage-badge").innerText = `${result.dunning_stage} (${result.action_taken})`;
    document.getElementById("b2b-dunning-copy-box").innerText = result.dunning_notice_copy;

    if (window.lucide) {
      lucide.createIcons();
    }
  } catch (err) {
    alert("Dunning execution failed: " + err.message);
  }
}

// Auto-load B2B invoices and Optimizer rails on init
setTimeout(() => {
  loadB2BInvoices();
  loadOptimizerRails();
}, 500);

// ==========================================
// Multi-Agent War Room Swarm Visualizer
// ==========================================

async function runSwarmWarRoom() {
  const btn = document.getElementById("btn-run-swarm");
  btn.innerHTML = `<span class="animate-spin inline-block mr-2">🔄</span> Swarm In Session...`;
  btn.disabled = true;

  const isOptedOut = document.getElementById("swarm-optout-toggle")?.checked || document.getElementById("input-optout")?.checked || false;

  const member = {
    member_id: "mem_blr_4091",
    name: document.getElementById("input-name")?.value || "Rahul Sharma",
    phone: document.getElementById("input-phone")?.value || "+919876543210",
    email: "rahul.sharma@example.com",
    language_preference: "hinglish",
    membership_tier: document.getElementById("input-tier")?.value || "QUARTERLY_PRO",
    membership_amount: parseFloat(document.getElementById("input-amount")?.value) || 6499.0,
    plan_start_date: "2026-06-01",
    plan_expiry_date: "2026-09-01",
    baseline_visits_per_week: 4.0,
    actual_visits_last_30_days: parseInt(document.getElementById("input-visits")?.value) || 2,
    days_since_last_checkin: parseInt(document.getElementById("input-days-inactive")?.value) || 18,
    lifetime_paid_inr: 15000.0,
    previous_payment_method: "UPI_AUTOPAY",
    consecutive_failed_attempts: parseInt(document.getElementById("input-fails")?.value) || 1,
    opted_out: isOptedOut,
    last_failure_code: document.getElementById("input-failure-code")?.value || "NONE"
  };

  try {
    const res = await fetch("/api/swarm/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(member)
    });
    const result = await res.json();

    const isVetoed = result.status === "STOPPED_BY_AUDITOR";
    const statusBadge = document.getElementById("swarm-status-badge");
    statusBadge.innerText = `Status: ${result.status} ${isVetoed ? '🛑 (VETO TRIGGERED)' : '| Rail: ' + (result.gateway_rail || 'N/A')}`;
    statusBadge.className = isVetoed ? "text-xs font-mono text-rose-400 font-bold" : "text-xs font-mono text-purple-400";

    // Visual Node Updates
    const executedStepRoles = (result.steps || []).map(s => s.agent_role);
    
    // Sentinel
    const nodeSentinel = document.getElementById("node-sentinel");
    const dotSentinel = document.getElementById("dot-sentinel");
    nodeSentinel.className = "p-4 bg-slate-900 rounded-2xl border border-blue-500/50 space-y-2 relative shadow-lg shadow-blue-500/10";
    dotSentinel.className = "w-2.5 h-2.5 rounded-full bg-blue-400";

    // Forensic
    const nodeForensic = document.getElementById("node-forensic");
    const dotForensic = document.getElementById("dot-forensic");
    nodeForensic.className = "p-4 bg-slate-900 rounded-2xl border border-purple-500/50 space-y-2 relative shadow-lg shadow-purple-500/10";
    dotForensic.className = "w-2.5 h-2.5 rounded-full bg-purple-400";

    // Auditor
    const nodeAuditor = document.getElementById("node-auditor");
    const dotAuditor = document.getElementById("dot-auditor");
    if (isVetoed) {
      nodeAuditor.className = "p-4 bg-rose-950/40 rounded-2xl border border-rose-500 space-y-2 relative shadow-xl shadow-rose-500/20";
      dotAuditor.className = "w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping";
    } else {
      nodeAuditor.className = "p-4 bg-slate-900 rounded-2xl border border-emerald-500/50 space-y-2 relative shadow-lg shadow-emerald-500/10";
      dotAuditor.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";
    }

    // Negotiator & Settlement
    const nodeNegotiator = document.getElementById("node-negotiator");
    const dotNegotiator = document.getElementById("dot-negotiator");
    const nodeSettlement = document.getElementById("node-settlement");
    const dotSettlement = document.getElementById("dot-settlement");

    if (isVetoed) {
      // Deactivated when vetoed
      nodeNegotiator.className = "p-4 bg-slate-950/60 rounded-2xl border border-slate-800 space-y-2 relative opacity-30";
      dotNegotiator.className = "w-2.5 h-2.5 rounded-full bg-slate-700";

      nodeSettlement.className = "p-4 bg-slate-950/60 rounded-2xl border border-slate-800 space-y-2 relative opacity-30";
      dotSettlement.className = "w-2.5 h-2.5 rounded-full bg-slate-700";
    } else {
      nodeNegotiator.className = "p-4 bg-slate-900 rounded-2xl border border-emerald-500/50 space-y-2 relative shadow-lg shadow-emerald-500/10";
      dotNegotiator.className = "w-2.5 h-2.5 rounded-full bg-emerald-400";

      nodeSettlement.className = "p-4 bg-slate-900 rounded-2xl border border-cyan-500/50 space-y-2 relative shadow-lg shadow-cyan-500/10";
      dotSettlement.className = "w-2.5 h-2.5 rounded-full bg-cyan-400";
    }

    // Populate Stream
    const feed = document.getElementById("swarm-feed-container");
    feed.innerHTML = "";

    (result.steps || []).forEach(step => {
      const isStepVeto = step.status === "VETOED";
      const stepCard = document.createElement("div");
      stepCard.className = `p-4 rounded-xl border space-y-2 ${isStepVeto ? 'bg-rose-950/30 border-rose-500/50' : 'bg-slate-900/90 border-slate-800'}`;
      
      const rolePretty = (step.agent_role || "").replace(/_/g, " ");
      const formattedJson = JSON.stringify(step.output_produced || {}, null, 2);

      stepCard.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 pb-1 border-b border-slate-800/60">
          <div class="flex items-center gap-2 flex-wrap min-w-0">
            <span class="px-2 py-0.5 rounded ${isStepVeto ? 'bg-rose-500/20 text-rose-300' : 'bg-purple-500/20 text-purple-300'} font-bold text-[10px] font-mono shrink-0">
              ${step.agent_name}
            </span>
            <span class="text-[11px] font-semibold ${isStepVeto ? 'text-rose-300' : 'text-slate-200'}">
              ${rolePretty}
            </span>
            ${isStepVeto ? '<span class="px-1.5 py-0.2 rounded bg-rose-500/30 text-rose-300 font-mono text-[9px] shrink-0">🛑 VETOED</span>' : '<span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 font-mono text-[9px] shrink-0">✓ COMPLETED</span>'}
          </div>
          <span class="text-slate-400 font-mono text-[10px] shrink-0 whitespace-nowrap">${formatIST(step.timestamp)}</span>
        </div>
        <div class="text-xs text-slate-200 font-sans leading-relaxed break-words">
          ${escapeHtml(step.reasoning_trace)}
        </div>
        <div class="text-[10px] font-mono text-cyan-300 bg-[#060a12] p-2.5 rounded-lg mt-1 border border-slate-800/80 overflow-x-auto whitespace-pre-wrap break-all max-h-[160px] overflow-y-auto">
          <div class="text-[9px] text-slate-500 font-bold uppercase tracking-wider mb-1">Payload Output:</div>
          ${escapeHtml(formattedJson)}
        </div>
      `;
      feed.appendChild(stepCard);
    });

    if (isVetoed) {
      const vetoNotice = document.createElement("div");
      vetoNotice.className = "p-3 bg-rose-950/60 border border-rose-500/40 rounded-xl text-xs text-rose-300 font-sans";
      vetoNotice.innerHTML = `🛑 <strong>Auditor Agent Veto Enforced:</strong> Compliance rules triggered (Opt-out detected). Execution halted at step 3. Negotiator & Settlement agents disabled to prevent unauthorized contact.`;
      feed.appendChild(vetoNotice);
    }

    if (window.lucide) {
      lucide.createIcons();
    }
  } catch (err) {
    alert("Swarm execution failed: " + err.message);
  } finally {
    btn.innerHTML = `<i data-lucide="sparkles" class="w-4 h-4 mr-2"></i><span>Execute 5-Agent War Room</span>`;
    btn.disabled = false;
    if (window.lucide) {
      lucide.createIcons();
    }
  }
}

// ==========================================
// Razorpay Optimizer & Smart Router
// ==========================================

async function loadOptimizerRails() {
  try {
    const res = await fetch("/api/optimizer/health");
    const data = await res.json();
    const container = document.getElementById("optimizer-rails-container");
    container.innerHTML = "";

    (data.rails || []).forEach(rail => {
      const isHealthy = rail.circuit_state === "CLOSED";
      const badgeColor = isHealthy ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30" : "bg-rose-500/10 text-rose-400 border-rose-500/30";

      const card = document.createElement("div");
      card.id = `card-${rail.rail_id}`;
      card.className = "p-5 bg-slate-900 rounded-2xl border border-slate-800 space-y-3 relative transition-all duration-300";
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">Priority ${rail.priority}</span>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}">${rail.circuit_state}</span>
        </div>
        <div>
          <h4 class="font-bold text-xs text-white">${rail.gateway_name}</h4>
          <span class="text-[10px] text-slate-500 font-mono">${rail.primary_protocol}</span>
        </div>
        <div class="space-y-1 text-[11px]">
          <div class="flex justify-between text-slate-400">
            <span>Success Rate</span>
            <span class="font-bold ${rail.success_rate_pct >= 90 ? 'text-emerald-400' : 'text-rose-400'}">${rail.success_rate_pct}%</span>
          </div>
          <div class="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
            <div class="h-full ${rail.success_rate_pct >= 90 ? 'bg-emerald-500' : 'bg-rose-500'}" style="width: ${rail.success_rate_pct}%"></div>
          </div>
          <div class="flex justify-between text-slate-400 pt-1">
            <span>Avg Latency</span>
            <span class="font-mono text-cyan-300">${rail.average_latency_ms}ms</span>
          </div>
          <div class="flex justify-between text-slate-400 pt-0.5 text-[10px]">
            <span>Routed GMV</span>
            <span class="font-mono text-slate-300 font-bold">₹${(rail.total_routed_volume_inr || 0).toLocaleString()}</span>
          </div>
        </div>
        <div class="pt-2 border-t border-slate-800/80">
          <button onclick="simulateOutage('${rail.rail_id}', ${isHealthy})" class="w-full py-1.5 px-2 rounded-lg text-[10px] font-bold transition flex items-center justify-center space-x-1 ${isHealthy ? 'bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 border border-rose-500/30' : 'bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border border-emerald-500/30'}">
            <span>${isHealthy ? '⚠️ Trip Outage' : '✓ Restore Healthy'}</span>
          </button>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Failed to load optimizer rails", err);
  }
}

async function simulateOutage(railId, trip) {
  try {
    const res = await fetch("/api/optimizer/simulate-outage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rail_id: railId, trip_circuit: trip })
    });
    await loadOptimizerRails();
  } catch (err) {
    alert("Outage simulation failed: " + err.message);
  }
}

async function simulateScenarioOutage(railsToTrip) {
  const allRails = ["rail_hdfc", "rail_icici", "rail_axis", "rail_dynamic_qr"];
  for (const r of allRails) {
    const shouldTrip = railsToTrip.includes(r);
    await fetch("/api/optimizer/simulate-outage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rail_id: r, trip_circuit: shouldTrip })
    });
  }
  await loadOptimizerRails();
  await testRouteTransaction();
}

async function restoreAllRails() {
  const allRails = ["rail_hdfc", "rail_icici", "rail_axis", "rail_dynamic_qr"];
  for (const r of allRails) {
    await fetch("/api/optimizer/simulate-outage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rail_id: r, trip_circuit: false })
    });
  }
  await loadOptimizerRails();
  await testRouteTransaction();
}

async function testRouteTransaction() {
  const btn = document.getElementById("btn-route-optimizer");
  if (btn) {
    btn.innerHTML = `<span class="animate-spin inline-block mr-2">⚡</span> Routing via Optimizer...`;
    btn.disabled = true;
  }

  const amtSelect = document.getElementById("optimizer-test-amount");
  const testAmt = amtSelect ? parseFloat(amtSelect.value) : 6499.0;

  try {
    const res = await fetch("/api/optimizer/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ amount_inr: testAmt })
    });
    const result = await res.json();

    // Reload rails to show updated Routed GMV volume
    await loadOptimizerRails();

    // Highlight selected rail card
    const allRailIds = ["rail_hdfc", "rail_icici", "rail_axis", "rail_dynamic_qr"];
    allRailIds.forEach(id => {
      const c = document.getElementById(`card-${id}`);
      if (c) c.classList.remove("ring-2", "ring-cyan-400", "shadow-xl", "shadow-cyan-500/20");
    });
    const activeCard = document.getElementById(`card-${result.selected_rail_id}`);
    if (activeCard) {
      activeCard.classList.add("ring-2", "ring-cyan-400", "shadow-xl", "shadow-cyan-500/20");
    }

    const txId = "txn_opt_" + Math.random().toString(36).substring(2, 9);
    const nowTime = new Date().toLocaleTimeString();

    const box = document.getElementById("optimizer-route-result");
    box.classList.remove("hidden");
    box.innerHTML = `
      <div class="flex items-center justify-between font-bold pb-1 border-b border-slate-800">
        <span class="text-emerald-400 flex items-center space-x-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
          <span>Routing Execution Live</span>
        </span>
        <span class="px-2.5 py-0.5 rounded text-[10px] ${result.failover_triggered ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'}">
          ${result.failover_triggered ? '⚠️ DYNAMIC FAILOVER ACTIVE' : '✓ PRIMARY DIRECT ROUTED'}
        </span>
      </div>
      <div class="space-y-1 text-slate-300 pt-1">
        <div>• <strong>Transaction ID:</strong> <span class="font-mono text-cyan-300">${txId}</span> (₹${testAmt.toLocaleString()} at ${nowTime})</div>
        <div>• <strong>Active Gateway:</strong> <span class="text-white font-bold">${result.gateway_name}</span> (${result.protocol_used})</div>
        <div>• <strong>Network Performance:</strong> <span class="text-cyan-300">${result.expected_latency_ms}ms latency</span> | <span class="text-emerald-400 font-bold">${result.gateway_success_rate}% Success Rate</span></div>
        <div>• <strong>Routing Policy:</strong> <span class="text-purple-300">${result.routing_reason}</span></div>
      </div>
    `;
  } catch (err) {
    alert("Routing test failed: " + err.message);
  } finally {
    if (btn) {
      btn.innerHTML = `<i data-lucide="send" class="w-4 h-4 mr-2"></i><span>Dispatch & Route Transaction Through Live Optimizer</span>`;
      btn.disabled = false;
    }
    if (window.lucide) {
      lucide.createIcons();
    }
  }
}


