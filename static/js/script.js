document.addEventListener('DOMContentLoaded', () => {

    // --- いいねボタンの処理 ---
    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const postId = button.dataset.postId;
            try {
                const response = await fetch(`/like/${postId}`, { method: 'POST' });
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();

                if (data.success) {
                    button.classList.toggle('active', data.liked);
                    // アイコンを♥と♡で切り替える
                    button.textContent = data.liked ? '♥' : '♡';

                    // テーブルの行(tr)からいいね数の要素を探して更新する
                    const row = button.closest('tr');
                    const countSpan = row.querySelector('.likes-cell .like-count');
                    if (countSpan) {
                        countSpan.textContent = data.count;
                    }
                }
            } catch (error) {
                console.error('Like action failed:', error);
            }
        });
    });

    // --- お気に入りボタンの処理 ---
    document.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const postId = button.dataset.postId;
            const row = button.closest('tr');

            try {
                const response = await fetch(`/favorite/${postId}`, { method: 'POST' });
                if (!response.ok) throw new Error('Network response was not ok');
                const data = await response.json();

                if (data.success) {
                    button.classList.toggle('active', data.favorited);
                    // アイコンを★と☆で切り替える
                    button.textContent = data.favorited ? '★' : '☆';

                    // お気に入り一覧ページでお気に入り解除した場合、その行を非表示にする
                    if (window.location.pathname.includes('/favorites') && !data.favorited) {
                        row.style.transition = 'opacity 0.5s';
                        row.style.opacity = '0';
                        setTimeout(() => row.remove(), 500);
                    }
                }
            } catch (error) {
                console.error('Favorite action failed:', error);
            }
        });
    });

});
