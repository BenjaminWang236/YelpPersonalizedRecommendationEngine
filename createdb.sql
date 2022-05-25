CREATE TABLE Users(
    uid CHAR(22) PRIMARY KEY,
    uname VARCHAR(50),
    yelping_since DATE,
    review_count INTEGER,
    avg_stars DECIMAL
);

CREATE TABLE Businesses(
    bid CHAR(22) PRIMARY KEY,
    if_open BOOLEAN,
    city VARCHAR(30),
    b_state CHAR(3),
    review_count INTEGER,
    bname VARCHAR(100),
    stars DECIMAL
);

CREATE TABLE Categories(
    bid CHAR(22) NOT NULL,
    catg VARCHAR(40),
    PRIMARY KEY (bid, catg),
    FOREIGN KEY (bid) REFERENCES Businesses (bid) ON DELETE CASCADE
);


CREATE TABLE Subcategories(
    bid CHAR(22) NOT NULL,
    subcatg VARCHAR(40),
    PRIMARY KEY (bid, subcatg),
    FOREIGN KEY (bid) REFERENCES Businesses (bid) ON DELETE CASCADE
);

CREATE TABLE Attributes(
    bid CHAR(22) NOT NULL, 
    attribute VARCHAR(50),
    PRIMARY KEY (bid, attribute),
    FOREIGN KEY (bid) REFERENCES Businesses (bid) ON DELETE CASCADE
);

CREATE TABLE Reviews(
    rid CHAR(22) PRIMARY KEY,
    uid CHAR(22) NOT NULL, 
    bid CHAR(22) NOT NULL,
    useful_vote_count INTEGER,
    stars DECIMAL,
    rdate DATE,
    content TEXT,
    FOREIGN KEY (uid) REFERENCES Users (uid) ON DELETE CASCADE,
    FOREIGN KEY (bid) REFERENCES Businesses(bid) ON DELETE CASCADE
);

CREATE TABLE Photos (
    pid CHAR(22) PRIMARY KEY,
    bid CHAR(22) NOT NULL,
    FOREIGN KEY (bid) REFERENCES Businesses(bid) ON DELETE CASCADE
);

CREATE INDEX category_catg_i on Categories (catg);
CREATE INDEX subcategory_subcatg_i on Subcategories (subcatg);
CREATE INDEX attribute_attribute_i on Attributes (attribute);


CREATE INDEX user_stars_i on Users (avg_stars);
CREATE INDEX user_review_i on Users (review_count);
CREATE INDEX user_vote_i on Users (vote_count);
CREATE INDEX user_friend_i on Users (friend_count);
CREATE INDEX user_date_i on Users (yelping_since);



CREATE INDEX review_yid_i on Reviews (uid);
CREATE INDEX review_bid_i on Reviews (bid);
CREATE INDEX review_date_i on Reviews (rdate);
CREATE INDEX review_vote_i on Reviews (useful_vote_count);
CREATE INDEX review_stars_i on Reviews (stars);
