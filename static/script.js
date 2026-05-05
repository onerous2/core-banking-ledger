const API_URL = window.location.origin;

// 1. Загрузка списка счетов (ОБНОВЛЕННАЯ ВЕРСИЯ)
async function loadAccounts() {
    try {
        const response = await fetch(`${API_URL}/accounts/`);
        const accounts = await response.json();
        const listElement = document.getElementById('accounts-list');
        listElement.innerHTML = '';

        accounts.forEach(acc => {
            const card = document.createElement('div');
            card.className = 'account-card';
            
            // Заменяем старый внутренний HTML на новый с оберткой card-actions и двумя кнопками
            card.innerHTML = `
                <button class="delete-btn" onclick="deleteAccount(${acc.id})" title="Закрыть счет">✖</button>
                <div><strong>ID: ${acc.id}</strong></div>
                <div style="margin: 5px 0; color: #64748b;">${acc.owner_name}</div>
                <div class="balance">${acc.balance.toLocaleString()} $</div>
                <div class="card-actions">
                    <button class="deposit-btn" onclick="makeDeposit(${acc.id})">Пополнить</button>
                    <button class="history-btn" onclick="showHistory(${acc.id})">📜 История</button>
                </div>
            `;
            listElement.appendChild(card);
        });
    } catch (err) {
        console.error("Ошибка загрузки данных:", err);
    }
}

// 2. Управление модальным окном
function openModal() { document.getElementById('modal').style.display = 'flex'; }
function closeModal() { 
    document.getElementById('modal').style.display = 'none';
    document.getElementById('new-owner-name').value = '';
}

// 3. Создание счета
async function createAccount() {
    const name = document.getElementById('new-owner-name').value;
    if (!name) return alert("Введите имя и фамилию!");

    const response = await fetch(`${API_URL}/accounts/?owner_name=${encodeURIComponent(name)}`, {
        method: 'POST'
    });

    if (response.ok) {
        closeModal();
        loadAccounts();
    }
}

// 4. Пополнение счета
async function makeDeposit(id) {
    const amount = prompt("Введите сумму пополнения:");
    if (!amount || isNaN(amount) || amount <= 0) return;

    const response = await fetch(`${API_URL}/accounts/${id}/deposit?amount=${amount}`, {
        method: 'POST'
    });

    if (response.ok) {
        loadAccounts();
    }
}

// 5. Удаление (закрытие) счета
async function deleteAccount(id) {
    if (!confirm(`Вы уверены, что хотите закрыть счет ID ${id}?`)) return;

    const response = await fetch(`${API_URL}/accounts/${id}`, {
        method: 'DELETE'
    });

    if (response.ok) {
        loadAccounts();
    }
}

// 6. Перевод между счетами
async function makeTransfer() {
    const fromId = document.getElementById('from-id').value;
    const toId = document.getElementById('to-id').value;
    const amount = document.getElementById('amount').value;

    if (!fromId || !toId || !amount) return alert("Заполните все поля!");

    const response = await fetch(`${API_URL}/transfer/?from_id=${fromId}&to_id=${toId}&amount=${amount}`, {
        method: 'POST'
    });

    if (response.ok) {
        alert("✅ Перевод выполнен успешно!");
        loadAccounts();
    } else {
        const err = await response.json();
        alert("❌ Ошибка: " + (err.detail || "Не удалось выполнить перевод"));
    }
}

// Первичная загрузка
loadAccounts();

async function showHistory(id) {
    const response = await fetch(`${API_URL}/accounts/${id}/history`);
    const history = await response.json();
    
    const container = document.getElementById('history-content');
    
    if (history.length === 0) {
        container.innerHTML = "<p>Операций пока нет</p>";
    } else {
        let tableHtml = `
            <table style="width: 100%; border-collapse: collapse; text-align: left;">
                <tr style="border-bottom: 2px solid #f1f5f9; color: #64748b; font-size: 0.9rem;">
                    <th style="padding: 10px 5px;">Время</th>
                    <th>Описание</th>
                    <th style="text-align: right;">Сумма</th>
                </tr>
        `;
        
        history.forEach(h => {
            const color = h.amount > 0 ? "#10b981" : "#ef4444";
            const prefix = h.amount > 0 ? "+" : "";
            tableHtml += `
                <tr style="border-bottom: 1px solid #f8fafc;">
                    <td style="padding: 12px 5px; font-size: 0.85rem; color: #94a3b8;">${h.date}</td>
                    <td style="font-size: 0.9rem;">${h.description}</td>
                    <td style="text-align: right; font-weight: 600; color: ${color}">${prefix}${h.amount.toLocaleString()} ₽</td>
                </tr>
            `;
        });
        
        tableHtml += "</table>";
        container.innerHTML = tableHtml;
    }
    
    document.getElementById('history-modal').style.display = 'flex';
}

function closeHistory() {
    document.getElementById('history-modal').style.display = 'none';
}