document.addEventListener("DOMContentLoaded", function() {
    const likeButtons = document.querySelectorAll('.like-button');
    const unlikeButtons = document.querySelectorAll('.unlike-button');

    likeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.id;  // Changed from dataset.postId to dataset.id
            fetch(`/like_post/${postId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
            }).then(response => response.json())
              .then(data => {
                  // Update likes count
                  if (data.likes_count !== undefined) {
                      this.nextElementSibling.textContent = `${data.likes_count} Likes`;
                  } else {
                      console.error("Error liking the post: ", data.message);
                  }
              })
              .catch(error => console.error('Error:', error));
        });
    });

    unlikeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const postId = this.dataset.id;  // Changed from dataset.postId to dataset.id
            fetch(`/unlike_post/${postId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
            }).then(response => response.json())
              .then(data => {
                  // Update likes count
                  if (data.likes_count !== undefined) {
                      this.previousElementSibling.textContent = `${data.likes_count} Likes`;
                  } else {
                      console.error("Error unliking the post: ", data.message);
                  }
              })
              .catch(error => console.error('Error:', error));
        });
    });
});
