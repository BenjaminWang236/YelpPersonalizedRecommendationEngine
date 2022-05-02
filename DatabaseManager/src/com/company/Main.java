package com.company;
import org.json.simple.JSONArray;
import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.text.SimpleDateFormat;
import java.util.HashSet;
import java.util.Set;


public class Main {
    private static final String PUBLIC_DNS = "database-1.c50spqkkfz7j.us-west-1.rds.amazonaws.com";
    private static final String PORT = "3306";
    private static final String DB_URL = "jdbc:mysql://" + PUBLIC_DNS + ":" + PORT + "/db";
    private static final String USER_NAME = "admin";
    private static final String PASSWORD = "606HaoYunLai606!";

    private static Connection conn = null;
    private static Set<String> catgSet;
    private static JSONParser jsonParser;

    public static void main(String[] args) {
	    connectJdbcToAwsRdb();
	    if (conn != null) {
	        populateTables();
        }
    }

    private static void connectJdbcToAwsRdb() {
        System.out.println("----MySQL JDBC Connection Testing -------");
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
            conn = DriverManager.getConnection(DB_URL, USER_NAME, PASSWORD);
            if (conn != null) {
                System.out.println("SUCCESS!!!! You made it, take control of your database now!");
            } else {
                System.out.println("FAILURE! Failed to make connection!");
            }
        } catch (ClassNotFoundException e) {
            System.out.println("Cannot find MySQL JDBC Driver");
            e.printStackTrace();
        } catch (SQLException e) {
            System.out.println("Connection failed");
            e.printStackTrace();
        }
    }

    private static void populateTables() {
        createCatgSet();
        jsonParser = new JSONParser();
//        populateUsers();
//        populateBusinesses();
//        populateCategories();
//        populateSubcategories();
        populateAttributes();
//        populateReviews();
    }

    private static void populateUsers() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT INTO Users VALUES (?,?,?,?,?,?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_user.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    stmt.setString(1, jsonObject.get("user_id").toString());
                    stmt.setString(2, jsonObject.get("name").toString());
                    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM");
                    java.util.Date date = sdf.parse(jsonObject.get("yelping_since").toString());
                    java.sql.Date sqlDate = new java.sql.Date(date.getTime());
                    stmt.setDate(3, sqlDate);
                    stmt.setInt(4, Integer.parseInt(jsonObject.get("review_count").toString()));
                    JSONArray friends = (JSONArray) jsonObject.get("friends");
                    stmt.setInt(5, friends.size());
                    stmt.setDouble(6, (double) jsonObject.get("average_stars"));
                    JSONObject voteObj = (JSONObject) jsonObject.get("votes");
                    int voteCount = Integer.parseInt(voteObj.get("funny").toString())
                            + Integer.parseInt(voteObj.get("useful").toString())
                            + Integer.parseInt(voteObj.get("cool").toString());
                    stmt.setInt(7, voteCount);
                    stmt.executeUpdate();
                }
                br.close();
                file.close();
                stmt.close();
                System.out.println("Table Users is populated with data!");
            } catch (IOException | ParseException | java.text.ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void populateBusinesses() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT INTO Businesses VALUES (?,?,?,?,?,?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_business.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    stmt.setString(1, jsonObject.get("business_id").toString());
                    String ifOpen = jsonObject.get("open").toString();
                    if (ifOpen.equals("true")) {
                        stmt.setInt(2, 1);
                    } else {
                        stmt.setInt(2, 0);
                    }
                    stmt.setString(3, jsonObject.get("city").toString());
                    stmt.setString(4, jsonObject.get("state").toString());
                    stmt.setInt(5, Integer.parseInt(jsonObject.get("review_count").toString()));
                    stmt.setString(6, jsonObject.get("name").toString());
                    stmt.setDouble(7, (double) jsonObject.get("stars"));
                    stmt.executeUpdate();
                }
                br.close();
                file.close();
                stmt.close();
                System.out.println("Table Businesses is populated with data!");
            } catch (IOException | ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void populateCategories() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT INTO Categories VALUES (?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_business.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    String bid = jsonObject.get("business_id").toString();
                    JSONArray jsonArray = (JSONArray) jsonObject.get("categories");
                    for (Object o : jsonArray) {
                        String catg = o.toString();
                        if (catgSet.contains(catg)) {
                            stmt.setString(1, bid);
                            stmt.setString(2, catg);
                            stmt.executeUpdate();
                        }
                    }
                }
                br.close();
                file.close();
                System.out.println("Table Categories is populated with data!");
            } catch (IOException | ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void populateSubcategories() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT INTO Subcategories VALUES (?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_business.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    String bid = jsonObject.get("business_id").toString();
                    JSONArray jsonArray = (JSONArray) jsonObject.get("categories");
                    for (Object o : jsonArray) {
                        String subcatg = o.toString();
                        if (!catgSet.contains(subcatg)) {
                            stmt.setString(1, bid);
                            stmt.setString(2, subcatg);
                            stmt.executeUpdate();
                        }
                    }
                }
                br.close();
                file.close();
                stmt.close();
                System.out.println("Table SubCategories is populated with data!");
            } catch (IOException | ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void populateAttributes() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT IGNORE INTO Attributes VALUES (?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_business.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    String bid = jsonObject.get("business_id").toString();
                    JSONObject attributeObj = (JSONObject) jsonObject.get("attributes");
                    for (String key : (Iterable<String>) attributeObj.keySet()) {
                        if (attributeObj.get(key) instanceof JSONObject) {
                            JSONObject nestedAttributeObj = (JSONObject) attributeObj.get(key);
                            for (String nestedKey : (Iterable<String>) nestedAttributeObj.keySet()) {
                                String nestedValue = nestedAttributeObj.get(nestedKey).toString();
                                stmt.setString(1, bid);
                                stmt.setString(2, nestedKey + "_" + nestedValue);
                                stmt.executeUpdate();
                            }
                        } else {
                            String value = attributeObj.get(key).toString();
                            stmt.setString(1, bid);
                            stmt.setString(2, key + "_" + value);
                            stmt.executeUpdate();
                        }
                    }
                }
                br.close();
                file.close();
                stmt.close();
                System.out.println("Table Attributes is populated with data!");
            } catch (IOException | ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void populateReviews() {
        try (PreparedStatement stmt = conn.prepareStatement("INSERT INTO Reviews VALUES (?,?,?,?,?,?,?)")) {
            try (FileReader file = new FileReader("YelpDataset-CptS451/yelp_review.json")) {
                BufferedReader br = new BufferedReader(file);
                String line;
                while ((line = br.readLine()) != null) {
                    JSONObject jsonObject = (JSONObject) jsonParser.parse(line);
                    stmt.setString(1, jsonObject.get("review_id").toString());
                    stmt.setString(2, jsonObject.get("user_id").toString());
                    stmt.setString(3, jsonObject.get("business_id").toString());
                    JSONObject votesObj = (JSONObject) jsonObject.get("votes");
                    stmt.setInt(4, Integer.parseInt(votesObj.get("useful").toString()));

                    stmt.setDouble(5, Double.parseDouble(jsonObject.get("stars").toString()));

                    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
                    java.util.Date date = sdf.parse(jsonObject.get("date").toString());
                    java.sql.Date sqlDate = new java.sql.Date(date.getTime());
                    stmt.setDate(6, sqlDate);
                    String content = jsonObject.get("text").toString();
                    content = content.length() > 500 ? content.substring(0, 500) : content;
                    stmt.setString(7, content);
                    stmt.executeUpdate();
                }
                br.close();
                file.close();
                stmt.close();
                System.out.println("Table Reviews is populated with data!");
            } catch (IOException | ParseException | java.text.ParseException e) {
                e.printStackTrace();
            }
        } catch (SQLException err) {
            err.printStackTrace();
        }
    }

    private static void createCatgSet(){
        catgSet = new HashSet<>();
        catgSet.add("Active Life");
        catgSet.add("Arts & Entertainment");
        catgSet.add("Automotive");
        catgSet.add("Car Rental");
        catgSet.add("Cafes");
        catgSet.add("Beauty & Spas");
        catgSet.add("Convenience Stores");
        catgSet.add("Dentists");
        catgSet.add("Doctors");
        catgSet.add("Drugstores");
        catgSet.add("Department Stores");
        catgSet.add("Education");
        catgSet.add("Event Planning & Services");
        catgSet.add("Flowers & Gifts");
        catgSet.add("Food");
        catgSet.add("Health & Medical");
        catgSet.add("Home Services");
        catgSet.add("Home & Garden");
        catgSet.add("Hospitals");
        catgSet.add("Hotels & Travel");
        catgSet.add("Hardware Stores");
        catgSet.add("Grocery");
        catgSet.add("Medical Centers");
        catgSet.add("Nurseries & Gardening");
        catgSet.add("Nightlife");
        catgSet.add("Restaurants");
        catgSet.add("Shopping");
        catgSet.add("Transportation");
    }
}
