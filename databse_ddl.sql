-- Create Organization Table
USE se_project;
CREATE TABLE Organization (
    OrganizationID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    ContactInformation VARCHAR(255) NOT NULL,
    Description TEXT,
    Location VARCHAR(255) NOT NULL
);
-- Create User Table
CREATE TABLE User (
    UserID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Email VARCHAR(255) UNIQUE NOT NULL,
    Role ENUM('sponsor', 'organiser') NOT NULL,
    Password VARCHAR(255) NOT NULL,
    OrganizationID INT,
    FOREIGN KEY (OrganizationID) REFERENCES Organization(OrganizationID)
);


-- Create Post Table (Parent Entity for Issues and Projects)
-- CREATE TABLE Post (
--     PostID INT AUTO_INCREMENT PRIMARY KEY,
--     Title VARCHAR(255) NOT NULL,
--     Description TEXT,
--     CreatedAtDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     Status VARCHAR(20) DEFAULT 'in progress',
--     Topic ENUM('environment', 'social','governance') NOT NULL,
--     UserID INT,
--     Upvotes INT DEFAULT 0,
--     Downvotes INT DEFAULT 0,
--     OrganizationID INT DEFAULT NULL,
--     Type ENUM('issue', 'project') DEFAULT 'issue',
--     FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
--     FOREIGN KEY (OrganizationID) REFERENCES Organization(OrganizationID)
-- );

CREATE TABLE Event (
    EventID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Location VARCHAR(255) NOT NULL,
    footfall INT NOT NULL,
	popularity_factor TEXT,
    Description TEXT,
    EventDate TIMESTAMP,
    CreatedAtDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Status VARCHAR(20) DEFAULT 'scheduled',
    Topic ENUM("music", 
				"business",
                "food_drink",
                "community_culture",
                "performing_visual_arts",
                "film_media_entertainment",
                "sports_fitness",
                "health_wellness",
                "science_technology",
                "travel_outdoor",
                "charity_causes",
                "religion_spirituality",              
                "family_education",
                "seasonal_holiday",
                "government_politics",
                "fashion_beauty",
                "home_lifestyle",
                "auto_boat_air",
                "hobbies_special_interests") NOT NULL,
	OrganizerID INT,
    PackageID INT,
    EventType ENUM('conference', 'seminar', 'workshop', 'cultural', 'sports', 'concert', 'fashion show') DEFAULT 'concert',
    FOREIGN KEY (OrganizerID) REFERENCES User(UserID) ON DELETE CASCADE,
    FOREIGN KEY (PackageID) REFERENCES Package(PackageID)
);

CREATE TABLE Package (
    PackageID INT AUTO_INCREMENT PRIMARY KEY,
    OrganizerID INT,
    Name VARCHAR(255) NOT NULL,
    Price DECIMAL(10,2) NOT NULL,
    Details TEXT,
    FOREIGN KEY (OrganizerID) REFERENCES User(UserID) ON DELETE CASCADE
);
	
CREATE TABLE Interest (
	interactionID INT AUTO_INCREMENT PRIMARY KEY,
    SponsorID INT NOT NULL,
    OrganizerID INT NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    interaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted BOOLEAN
);

CREATE TABLE chat_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES sponsor_requests(id),
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);

-- Create Comment Table
-- CREATE TABLE Comment (
--     CommentID INT AUTO_INCREMENT PRIMARY KEY,
--     Content TEXT,
--     CreatedAtDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     UserID INT,
--     PostID INT,
--     FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
--     FOREIGN KEY (PostID) REFERENCES Post(PostID) ON DELETE CASCADE
-- );

-- Create Sentiment Analysis Table
-- CREATE TABLE SentimentAnalysis (
--     CommentID INT PRIMARY KEY,
--     Sentiment VARCHAR(20),
--     Confidence FLOAT,
--     AnalysisDate TIMESTAMP,
--     FOREIGN KEY (CommentID) REFERENCES Comment(CommentID) ON DELETE CASCADE
-- );

-- Create UserVotes Table for tracking user votes on posts
-- CREATE TABLE UserVotes (
--     VoteID INT AUTO_INCREMENT PRIMARY KEY,
--     UserID INT,
--     PostID INT,
--     VoteType ENUM('upvote', 'downvote') NOT NULL,
--     CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     UNIQUE (UserID, PostID),
--     FOREIGN KEY (UserID) REFERENCES User(UserID) ON DELETE CASCADE,
--     FOREIGN KEY (PostID) REFERENCES Post(PostID) ON DELETE CASCADE
-- );

ALTER TABLE user
ADD COLUMN profile_pic LONGBLOB;

ALTER TABLE Organization
ADD COLUMN logo LONGBLOB;
