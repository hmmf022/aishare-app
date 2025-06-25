document.addEventListener('DOMContentLoaded', () => {

    const updateLikeCount = (button, newCount) => {
        const parentElement = button.closest('tr') || button.closest('.card');
        if (!parentElement) return;

        // テーブル用：いいね数のセルを探す
        let countSpan = parentElement.querySelector('.likes-cell .like-count');
        if (countSpan) {
            countSpan.textContent = newCount;
        }
        // カード用：ボタン内のspanを探す
        countSpan = button.querySelector('.like-count');
        if(countSpan) {
             countSpan.textContent = newCount;
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
                    // カード形式のボタンにはいいね数も含まれるので、アイコンだけ差し替える
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
