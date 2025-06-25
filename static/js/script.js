document.addEventListener('DOMContentLoaded', () => {

    const handleAction = async (button, url) => {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            if (!response.ok) throw new Error('Network response was not ok');

            const data = await response.json();

            if (data.success) {
                button.classList.toggle('active', data.liked ?? data.favorited);

                // いいね数の更新
                if (data.count !== undefined) {
                    const countSpan = button.querySelector('.like-count');
                    if (countSpan) {
                        countSpan.textContent = data.count;
                    }
                }
            }
        } catch (error) {
            console.error('Action failed:', error);
        }
    };

    document.querySelectorAll('.like-btn').forEach(button => {
        button.addEventListener('click', () => {
            const postId = button.dataset.postId;
            handleAction(button, `/like/${postId}`);
        });
    });

    document.querySelectorAll('.favorite-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            const postId = button.dataset.postId;
            const card = e.target.closest('.card');

            // お気に入りページでボタンを押した場合、カードを即時削除する
            if (window.location.pathname.includes('/favorites')) {
                card.style.display = 'none';
            }
            handleAction(button, `/favorite/${postId}`);
        });
    });
});
