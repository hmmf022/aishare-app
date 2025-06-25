document.addEventListener('DOMContentLoaded', () => {

    const updateLikeCount = (button, newCount) => {
        const parentElement = button.closest('tr') || button.closest('.card');
        if (!parentElement) return;

        let countSpanInCell = parentElement.querySelector('.likes-cell .like-count');
        if (countSpanInCell) {
            countSpanInCell.textContent = newCount;
        }
        let countSpanInButton = button.querySelector('.like-count');
        if(countSpanInButton) {
             countSpanInButton.textContent = newCount;
        }
    };

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
                    updateLikeCount(button, data.count);
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
});

if (window.location.pathname.includes('/admin')) {

    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', (e) => {
            const row = e.target.closest('tr');
            const postId = row.querySelector('.btn-delete').closest('form').action.split('/').pop();

            const titleCell = document.getElementById(`title-cell-${postId}`);
            const actionCell = document.getElementById(`action-cell-${postId}`);

            const currentTitle = titleCell.querySelector('a').textContent;
            const originalTitleHTML = titleCell.innerHTML;
            const originalActionsHTML = actionCell.innerHTML;

            // タイトルセルを編集フォームに切り替え
            titleCell.innerHTML = `<input type="text" class="title-edit-input" value="${currentTitle}">`;

            // アクションセルを「保存」「キャンセル」ボタンに切り替え
            actionCell.innerHTML = `
                <button type="button" class="btn-save">保存</button>
                <button type="button" class="btn-cancel">キャンセル</button>
            `;

            // --- キャンセルボタンの処理 ---
            actionCell.querySelector('.btn-cancel').addEventListener('click', () => {
                titleCell.innerHTML = originalTitleHTML;
                actionCell.innerHTML = originalActionsHTML;
                // イベントリスナーを再設定する必要があるため、少し複雑になるが、ここでは単純化
                // 実際は、イベント委譲を使うか、この関数を再実行するのが望ましい
                // 今回はページリロードで代用するのが最もシンプルで確実
                window.location.reload();
            });

            // --- 保存ボタンの処理 ---
            actionCell.querySelector('.btn-save').addEventListener('click', async () => {
                const newTitle = titleCell.querySelector('.title-edit-input').value;
                if (!newTitle || newTitle === currentTitle) {
                    actionCell.querySelector('.btn-cancel').click(); // 変更がなければキャンセルと同じ動作
                    return;
                }

                try {
                    const response = await fetch(`/admin/edit_title/${postId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ title: newTitle })
                    });

                    const result = await response.json();

                    if (result.success) {
                        // 成功したら表示を更新
                        titleCell.innerHTML = originalTitleHTML;
                        titleCell.querySelector('a').textContent = result.new_title;
                        actionCell.innerHTML = originalActionsHTML;
                        window.location.reload(); // 確実性を期してリロード
                    } else {
                        alert('エラー: ' + result.error);
                    }
                } catch (error) {
                    alert('タイトルの更新に失敗しました。');
                    console.error('Failed to edit title:', error);
                }
            });
        });
    });
}

// --- アコーディオンUIのロジック ---
// 共有ページ(/new)の場合のみ実行
if (window.location.pathname.includes('/new')) {
    document.querySelectorAll('.accordion-header').forEach(header => {
        header.addEventListener('click', () => {
            // クリックされたヘッダーに 'active' クラスを付け外し
            header.classList.toggle('active');

            const content = header.nextElementSibling;

            // コンテンツの表示/非表示を切り替え
            if (content.style.maxHeight) {
                // 閉じる
                content.style.maxHeight = null;
                content.style.padding = "0 1.5rem"; // paddingを即時変更
            } else {
                // 開く
                content.style.padding = "0 1.5rem"; // 開く前にpaddingを設定
                content.style.maxHeight = content.scrollHeight + "px";
            }
        });
    });
}
