import pandas as pd
import numpy as np

books = pd.read_csv("Books.csv")
ratings = pd.read_csv("Ratings.csv")
ratings_filtered = ratings[ratings["rating"] >= 4]
V = {}
for _, row in ratings_filtered.iterrows():
    user = row["user_id"]
    book = row["book_id"]
    V.setdefault(user, set()).add(book)

ballots = []
for user, books_set in V.items():
    ballots.append({
        "user_id": user,
        "movie_id": str(list(books_set))
    })

ballots_df = pd.DataFrame(ballots)
ballots_df = ballots_df.sort_values(by="user_id")
ballots_df.to_csv("approval_ballots.csv", index=False)
print("approval_ballots.csv created")
books["year_group"] = books["Publication Year"].apply(
    lambda x: "Old" if pd.notnull(x) and x < 2000 else "New"
)
books["pop_group"] = books["AvgRating"].apply(
    lambda x: int(np.floor(x)) if pd.notnull(x) else 0
)
author_counts = books["Author"].value_counts()
top_authors = author_counts.head(50).index
books["author_group"] = books["Author"].apply(
    lambda x: "TopAuthor" if x in top_authors else "Author"
)

attributes_df = books[[
    "book_id", "year_group", "pop_group", "author_group"
]].copy()
attributes_df.rename(columns={
    "book_id": "movie_id"
}, inplace=True)
attributes_df.to_csv("book_attributes.csv", index=False)

print("book_attributes.csv created")