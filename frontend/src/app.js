const API_URL = 'http://localhost:3000';

// Check server health
async function checkHealth() {
    const statusDiv = document.getElementById('status');
    statusDiv.innerHTML = '<p>상태 확인 중...</p>';
    
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        statusDiv.innerHTML = `
            <div class="status-success">
                <p><strong>상태:</strong> ${data.status}</p>
                <p><strong>메시지:</strong> ${data.message}</p>
                <p><strong>시간:</strong> ${new Date(data.timestamp).toLocaleString('ko-KR')}</p>
            </div>
        `;
    } catch (error) {
        statusDiv.innerHTML = `
            <p style="color: red;"><strong>오류:</strong> 서버에 연결할 수 없습니다.</p>
            <p>서버가 실행 중인지 확인하세요 (포트 3000)</p>
        `;
    }
}

// Fetch data from API
async function fetchData() {
    const dataDiv = document.getElementById('data-list');
    dataDiv.innerHTML = '<p>데이터를 불러오는 중...</p>';
    
    try {
        const response = await fetch(`${API_URL}/api/data`);
        const data = await response.json();
        
        if (data.items && data.items.length > 0) {
            dataDiv.innerHTML = data.items.map(item => `
                <div class="data-item">
                    <h3>${item.name}</h3>
                    <p><strong>ID:</strong> ${item.id}</p>
                    <p>${item.description}</p>
                </div>
            `).join('');
        } else {
            dataDiv.innerHTML = '<p>데이터가 없습니다.</p>';
        }
    } catch (error) {
        dataDiv.innerHTML = `
            <p style="color: red;"><strong>오류:</strong> 데이터를 불러올 수 없습니다.</p>
            <p>서버가 실행 중인지 확인하세요.</p>
        `;
    }
}

// Submit new data
async function submitData(event) {
    event.preventDefault();
    
    const form = document.getElementById('dataForm');
    const resultDiv = document.getElementById('form-result');
    const name = document.getElementById('name').value;
    const description = document.getElementById('description').value;
    
    resultDiv.classList.remove('show', 'success', 'error');
    
    try {
        const response = await fetch(`${API_URL}/api/data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name, description })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resultDiv.className = 'result-box show success';
            resultDiv.innerHTML = `
                <p><strong>성공!</strong> ${data.message}</p>
                <p><strong>ID:</strong> ${data.data.id}</p>
                <p><strong>생성 시간:</strong> ${new Date(data.data.createdAt).toLocaleString('ko-KR')}</p>
            `;
            form.reset();
        } else {
            throw new Error(data.error || '데이터 추가 실패');
        }
    } catch (error) {
        resultDiv.className = 'result-box show error';
        resultDiv.innerHTML = `
            <p><strong>오류:</strong> ${error.message}</p>
        `;
    }
}

// Check health on page load
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
});
