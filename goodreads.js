document.addEventListener('DOMContentLoaded', () => {
    const JSON_DATA_FILE = './bookshelf.json';
    async function loadBookshelf() {
        const currentlyReadingContainer = document.getElementById('current-books');
        const yearlyBooksContainer = document.getElementById('yearly-books-container'); 

        currentlyReadingContainer.innerHTML = '<p>Loading currently reading books...</p>';
        yearlyBooksContainer.innerHTML = '<p>Loading read books...</p>';

        try {
            const response = await fetch(JSON_DATA_FILE);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} when fetching ${JSON_DATA_FILE}`);
            }

            const allBooks = await response.json();

            displayCurrentlyReading(allBooks.currentlyReading);
            displayReadBooks(allBooks.readBooksByYear);

        } catch (error) {
            console.error('Error loading bookshelf data:', error);
            currentlyReadingContainer.innerHTML = '<p>Error loading books. Please try again later.</p>';
            yearlyBooksContainer.innerHTML = '<p>Error loading books. Please try again later.</p>';
        }
    }

    function displayCurrentlyReading(books) {
        const container = document.getElementById('current-books');
        container.innerHTML = ''; // Clear loading message

        if (books.length === 0) {
            container.innerHTML = '<p>No books currently being read.</p>';
            return;
        }

        books.forEach(book => {
            const bookDiv = document.createElement('div');
            bookDiv.classList.add('book-item');
            bookDiv.innerHTML = `
                <a href="${book.link}" target="_blank">
                    <img src="${book.imageUrl}" alt="${book.title}" width="75">
                </a>
                <div class="book-details">
                    <h3><a href="${book.link}" target="_blank">${book.title}</a></h3>
                    <p>by ${book.author}</p>
                </div>
            `;
            container.appendChild(bookDiv);
        });
    }

    function displayReadBooks(booksByYear) {
        const container = document.getElementById('yearly-books-container'); 
        container.innerHTML = ''; // Clear loading message

        // Sort years in descending order
        const sortedYears = Object.keys(booksByYear).sort((a, b) => b - a);

        if (sortedYears.length === 0) {
            container.innerHTML = '<p>No read books to display.</p>';
            return;
        }

        sortedYears.slice(0, 8).forEach(year => { // .slice(0, 2) trae solo este año y el pasado
            const yearSection = document.createElement('div');
            yearSection.classList.add('year-section');

            const yearHeader = document.createElement('h3');
            yearHeader.classList.add('year-header');

            const toggleButton = document.createElement('button');
            toggleButton.innerHTML = `&#9660;`;
            toggleButton.classList.add('toggle-button');
            toggleButton.setAttribute('data-year', year); 

            yearHeader.innerHTML = `${year} (${booksByYear[year].length} books) `; 
            yearHeader.appendChild(toggleButton); 

            const booksList = document.createElement('div');
            booksList.id = `books-${year}`;
            booksList.classList.add('books-list', 'hidden');

            const booksInYear = booksByYear[year];
            booksInYear.sort((a, b) => {
                const dateA = a.readAt ? new Date(a.readAt) : new Date(0);
                const dateB = b.readAt ? new Date(b.readAt) : new Date(0);
                return dateB - dateA; 
            });

            booksInYear.forEach(book => {
                const bookDiv = document.createElement('div');
                bookDiv.classList.add('book-item');
                bookDiv.innerHTML = `
                    <a href="${book.link}" target="_blank">
                        <img src="${book.imageUrl}" alt="${book.title}" width="75">
                    </a>
                    <div class="book-details">
                        <h3><a href="${book.link}" target="_blank">${book.title}</a></h3>
                        <p>by ${book.author}</p>
                    </div>
                `;
                booksList.appendChild(bookDiv);
            });
            
            yearSection.appendChild(yearHeader);
            yearSection.appendChild(booksList);
            container.appendChild(yearSection);
        });

        document.querySelectorAll('.toggle-button').forEach(button => {
            button.addEventListener('click', function() {
                const year = this.getAttribute('data-year');
                const booksList = document.getElementById(`books-${year}`);
                booksList.classList.toggle('hidden');

                if (booksList.classList.contains('hidden')) {
                    this.innerHTML = `&#9660;`;
                } else {
                    this.innerHTML = `&#9650;`;
                }
            });
        });
    }

    loadBookshelf();
});