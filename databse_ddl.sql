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

CREATE TABLE Interaction (
	chatbox_id INT AUTO_INCREMENT PRIMARY KEY
);

CREATE TABLE Chatbox (
    msg_id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message TEXT NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES Package(PackageID),
    FOREIGN KEY (sender_id) REFERENCES User(UserID),
    FOREIGN KEY (receiver_id) REFERENCES User(UserID)
);

CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    organiser_id INT NOT NULL,
    sponsor_id INT NOT NULL,
    event_id INT NOT NULL,
    rating INT,
    sponsorship_exhibitors VARCHAR(255),
    experienced_footfall VARCHAR(255),
    overall_satisfaction VARCHAR(255),
    communication VARCHAR(255),
    organization VARCHAR(255),
    venue VARCHAR(255),
    logistics VARCHAR(255),
    catering_food VARCHAR(255),
    technology_equipment VARCHAR(255),
    sustainability VARCHAR(255),
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organiser_id) REFERENCES Interaction (organiser_id),
    FOREIGN KEY (sponsor_id) REFERENCES Interaction (sponsor_id),
    FOREIGN KEY (event_id) REFERENCES Event (EventID)
);

ALTER TABLE user
ADD COLUMN profile_pic LONGBLOB;

alter table Package
add column Price_limit DECIMAL(10,2) NOT NULL;

alter table Package
drop column Details;
alter table Package
add column Description text;
alter table Package
add column EventID int;
alter table interaction
add constraint foreign key (EventID) references Event(EventID) on delete cascade;


alter table Chatbox
drop column package_id;
alter table Chatbox
add column box_id int;
alter table Chatbox
add constraint foreign key (box_id) references Interaction(chatbox_id) on delete cascade;

alter table interest
add column PackageID int not null;
alter table interest
add constraint foreign key (PackageID) references Package(PackageID) on delete cascade;

alter table interaction
add column sponsor_id int;

alter table interaction
add constraint foreign key (sponsor_id) references User(UserID) on delete cascade;

alter table interaction
add column organiser_id int;

alter table interaction
add constraint foreign key (organiser_id) references Package(OrganiserID) on delete cascade;

alter table interaction
add column package_id int;

alter table interaction
add constraint foreign key (package_id) references Package(PackageID) on delete cascade;

ALTER TABLE Organization
ADD COLUMN logo LONGBLOB;
