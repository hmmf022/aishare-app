document.addEventListener('DOMContentLoaded', () => {

    // --- いいね・お気に入りボタンの共通処理 ---
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const postId = button.dataset.postId;
            try {
                const response = await fetch(`/like/${postId}`, { method: 'POST' });
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                if (data.success) {
                    button.classList.toggle('active', data.liked);
                    const icon = data.liked ? '♥' : '♡';
                    const likeCountSpan = button.querySelector('.like-count');
                    if (likeCountSpan) {
                        button.innerHTML = `${icon}<span class="like-count">${data.count}</span>`;
                    } else {
                        button.textContent = icon;
                    }
                    const row = button.closest('tr');
                    if(row) {
                        const countSpanInCell = row.querySelector('.likes-cell .like-count');
                        if (countSpanInCell) countSpanInCell.textContent = data.count;
                    }
                }
            } catch (error) { console.error('Like action failed:', error); }
        });
    });

    document.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const postId = button.dataset.postId;
            const elementToRemove = button.closest('tr') || button.closest('.card');
            try {
                const response = await fetch(`/favorite/${postId}`, { method: 'POST' });
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();
                if (data.success) {
                    button.classList.toggle('active', data.favorited);
                    button.textContent = data.favorited ? '★' : '☆';
                    if (window.location.pathname.includes('/favorites') && !data.favorited && elementToRemove) {
                        elementToRemove.style.transition = 'opacity 0.5s, transform 0.5s';
                        elementToRemove.style.opacity = '0';
                        elementToRemove.style.transform = 'scale(0.95)';
                        setTimeout(() => elementToRemove.remove(), 500);
                    }
                }
            } catch (error) { console.error('Favorite action failed:', error); }
        });
    });

    // --- アコーディオンの共通ロジック ---
    function addAccordionEventListeners(selector) {
        const parentElement = document.querySelector(selector);
        if (!parentElement) return;

        parentElement.querySelectorAll('.accordion-header').forEach(header => {
            if (header.dataset.listenerAttached) return;

            header.addEventListener('click', () => {
                header.classList.toggle('active');
                const content = header.nextElementSibling;
                if (content.style.maxHeight) {
                    content.style.maxHeight = null;
                } else {
                    content.style.maxHeight = content.scrollHeight + "px";
                }
            });
            header.dataset.listenerAttached = 'true';
        });
    }

    // --- アコーディオンHTML生成ヘルパー ---
    function generateAccordionHTML(categories, selectedIds = []) {
        let html = '';
        categories.forEach(cat => {
            html += `<div class="accordion-item">
                <button type="button" class="accordion-header">
                    <span>${cat.category_name}</span><span class="accordion-icon">+</span>
                </button>
                <div class="accordion-content"><div class="tag-checkboxes">`;
            cat.tags.forEach(tag => {
                const isChecked = selectedIds.includes(tag.id);
                html += `<label><input type="checkbox" name="tags" value="${tag.id}" ${isChecked ? 'checked' : ''}> #${tag.name}</label>`;
            });
            html += `</div></div></div>`;
        });
        return html;
    }

    // --- 共有ページのアコーディオンを初期化 ---
    if(document.getElementById('new-post-form')) {
       addAccordionEventListeners('#new-post-form');
    }

    // --- 投稿者編集モーダルのロジック ---
    const editModalOverlay = document.getElementById('edit-modal-overlay');
    if (editModalOverlay) {
        const editForm = document.getElementById('edit-post-form');
        const editTitleInput = document.getElementById('edit-title');
        const editAccordionTags = document.getElementById('edit-accordion-tags');
        const cancelEditBtn = document.getElementById('cancel-edit-btn');
        let currentEditingPostId = null;
        let allCategorizedTags = null; // 全タグ情報をキャッシュ

        const openModal = async (postId) => {
            currentEditingPostId = postId;
            if (!allCategorizedTags) {
                try {
                    // ★★★【ここを修正】静的ファイルではなくAPIから取得する ★★★
                    const res = await fetch('/api/tags');
                    if(!res.ok) throw new Error('Failed to load tags data (HTTP status ' + res.status + ')');
                    allCategorizedTags = await res.json();
                } catch(e) {
                    alert('タグ情報の読み込みに失敗しました。リロードしてください。');
                    console.error("Error fetching tags from API:", e);
                    return;
                }
            }
            const detailsRes = await fetch(`/post/${postId}/details`);
            const postData = await detailsRes.json();
            if (!postData.success) { alert('投稿情報の取得に失敗しました。'); return; }

            editTitleInput.value = postData.title;
            editAccordionTags.innerHTML = generateAccordionHTML(allCategorizedTags, postData.selected_tags);
            addAccordionEventListeners('#edit-accordion-tags');
            editModalOverlay.style.display = 'flex';
        };

        document.querySelectorAll('.btn-edit-post').forEach(button => {
            button.addEventListener('click', (e) => openModal(e.currentTarget.dataset.postId));
        });

        const closeModal = () => {
            editModalOverlay.style.display = 'none';
            editForm.reset();
            currentEditingPostId = null;
        };
        cancelEditBtn.addEventListener('click', closeModal);
        editModalOverlay.addEventListener('click', (e) => { if (e.target === editModalOverlay) closeModal(); });

        editForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(editForm);
            const newTitle = formData.get('title');
            const newTags = Array.from(formData.getAll('tags'));
            const response = await fetch(`/post/${currentEditingPostId}/edit`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ title: newTitle, tags: newTags })
            });
            const result = await response.json();
            if (result.success) {
                alert('更新しました。');
                window.location.reload();
            } else {
                alert('エラー: ' + (result.error || '不明なエラーが発生しました。'));
            }
        });
    }

    // --- 管理画面のタイトルインライン編集機能 ---
    if (window.location.pathname.includes('/admin')) {
        document.querySelectorAll('.btn-admin-edit').forEach(button => {
            button.addEventListener('click', (e) => {
                const row = e.target.closest('tr');
                const postId = row.dataset.postId || row.querySelector('.btn-delete').closest('form').action.split('/').pop();
                const titleCell = document.getElementById(`title-cell-${postId}`);
                const actionCell = document.getElementById(`action-cell-${postId}`);
                const currentTitle = titleCell.querySelector('a').textContent;
                const originalActionsHTML = actionCell.innerHTML;

                titleCell.innerHTML = `<input type="text" class="title-edit-input" value="${currentTitle}">`;
                actionCell.innerHTML = `
                    <button type="button" class="btn-save btn-admin-save">保存</button>
                    <button type="button" class="btn-cancel btn-admin-cancel">キャンセル</button>
                `;
                actionCell.querySelector('.btn-admin-cancel').addEventListener('click', () => {
                    window.location.reload();
                });
                actionCell.querySelector('.btn-admin-save').addEventListener('click', async () => {
                    const newTitle = titleCell.querySelector('.title-edit-input').value;
                    if (!newTitle || newTitle === currentTitle) {
                        actionCell.querySelector('.btn-admin-cancel').click();
                        return;
                    }
                    try {
                        const response = await fetch(`/admin/edit_title/${postId}`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({ title: newTitle })
                        });
                        const result = await response.json();
                        if (result.success) {
                            window.location.reload();
                        } else { alert('エラー: ' + result.error); }
                    } catch (error) { alert('タイトルの更新に失敗しました。'); console.error('Failed to edit title:', error); }
                });
            });
        });
    }
});
