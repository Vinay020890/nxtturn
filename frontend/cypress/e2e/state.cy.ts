// C:\Users\Vinay\Project\frontend\cypress\e2e\state.cy.ts

describe('Application State Management', () => {

  /**
   * TEST CASE 1 (Definitive Version): This test is now 100% independent.
   * It creates its own user to guarantee that the feed is empty,
   * completely isolating it from the state of the database or other tests.
   * This is the gold standard for E2E testing.
   */
  it('should purge all store data on logout to prevent stale state', () => {
    // --- Step 1: Create a brand new, guaranteed-empty user just for this test ---
    const testUser = `testuser_${Date.now()}`;
    const testPass = 'Airtel@123';
    cy.createTestUser(testUser, testPass);

    // --- Part 2: Login as the existing user 'abc1' (who has posts) ---
    cy.visit('/login');
    cy.get('input[id="username"]').type('abc1');
    cy.get('input[id="password"]').type('Airtel@123');
    cy.get('button[type="submit"]').click();
    cy.url().should('not.include', '/login');
    // Verify abc1's posts are loaded as a baseline check
    cy.get('[data-cy="post-container"]').should('exist'); 

    // --- Part 3: Logout ---
    cy.get('[data-cy="logout-button"]').click();
    cy.url().should('include', '/login');

    // --- Part 4: Login as our NEWLY CREATED user and verify their empty feed ---
    cy.get('input[id="username"]').type(testUser);
    cy.get('input[id="password"]').type(testPass);
    cy.get('button[type="submit"]').click();
    cy.url().should('not.include', '/login');

    // Use the reliable wait to ensure the API call completes before asserting
    cy.intercept('GET', '**/api/feed/').as('getFeed');
    cy.visit('/');
    cy.wait('@getFeed');

    // The final, definitive assertion against a provably empty user
    cy.get('[data-cy="post-container"]').should('not.exist');
    cy.get('[data-cy="empty-feed-message"]').should('be.visible');
  });

  /**
   * TEST CASE 2 (Hardened Version): The reactivity test, now also using
   * an isolated user to prevent any possible test pollution.
   */
  it('should reflect a new post on the main feed and profile page instantly', () => {
    // Create a fresh user for this test to ensure perfect isolation
    const testUser = `reactiveuser_${Date.now()}`;
    const testPass = 'Airtel@123';
    cy.createTestUser(testUser, testPass);
    cy.login(testUser, testPass); // Programmatic login is faster and fine here
    
    cy.visit('/');
    
    const uniquePostText = `My reactive test post from Cypress at ${Date.now()}`;
    
    // Wait for the initial (empty) feed to load to avoid race conditions
    cy.intercept('GET', '**/api/feed/').as('getFeed');
    cy.wait('@getFeed');
    
    // Create the new post
    cy.get('[data-cy="create-post-input"]').type(uniquePostText);
    cy.get('[data-cy="create-post-submit-button"]').click();
    
    // Assert the post appears on the main feed
    cy.get('[data-cy="post-container"]').contains(uniquePostText).should('be.visible');
    
    // Navigate and assert the post also appears on the profile page
    cy.get('[data-cy="profile-link"]').click();
    cy.get('[data-cy="post-container"]').contains(uniquePostText).should('be.visible');
  });

  // Add this new 'it' block inside the describe('Application State Management', ...) in state.cy.ts

  it('should display only the correct posts on the main feed', () => {
    // --- 1. SETUP: Create three independent users for this test ---
    const mainUser = { username: `mainUser_${Date.now()}`, password: 'password123' };
    const followedUser = { username: `followed_${Date.now()}`, password: 'password123' };
    const otherUser = { username: `other_${Date.now()}`, password: 'password123' };

    cy.createTestUser(mainUser.username, mainUser.password);
    cy.createTestUser(followedUser.username, followedUser.password);
    cy.createTestUser(otherUser.username, otherUser.password);

    // --- 2. ACTIONS: Create posts for each user using the UI ---
    // This is robust as it also tests the post creation flow.
    const ownPostText = `This is my own post!`;
    const followedPostText = `Post from the user I follow.`;
    const otherPostText = `Post from a random user that should NOT be visible.`;

    // Create posts using our programmatic login for speed
    cy.login(mainUser.username, mainUser.password);
    cy.visit('/');
    cy.get('[data-cy="create-post-input"]').type(ownPostText);
    cy.get('[data-cy="create-post-submit-button"]').click();
    cy.get('[data-cy="post-container"]').contains(ownPostText).should('be.visible');

    cy.login(followedUser.username, followedUser.password);
    cy.visit('/');
    cy.get('[data-cy="create-post-input"]').type(followedPostText);
    cy.get('[data-cy="create-post-submit-button"]').click();
    cy.get('[data-cy="post-container"]').contains(followedPostText).should('be.visible');

    cy.login(otherUser.username, otherUser.password);
    cy.visit('/');
    cy.get('[data-cy="create-post-input"]').type(otherPostText);
    cy.get('[data-cy="create-post-submit-button"]').click();
    cy.get('[data-cy="post-container"]').contains(otherPostText).should('be.visible');

    // --- 3. THE CORE ACTION: Log in as mainUser and follow the target ---
    cy.login(mainUser.username, mainUser.password);
    cy.createFollow(mainUser.username, followedUser.username); // Programmatic follow

    // --- 4. ASSERTIONS: Visit the feed and check the content ---
    cy.visit('/');
    cy.intercept('GET', '**/api/feed/').as('getFeed');
    cy.wait('@getFeed');

    // Assert that the correct posts are visible
    cy.get('[data-cy="post-container"]').contains(ownPostText).should('be.visible');
    cy.get('[data-cy="post-container"]').contains(followedPostText).should('be.visible');
    
    // Assert that the incorrect post is NOT visible
    cy.get('body').should('not.contain', otherPostText);
  });
});