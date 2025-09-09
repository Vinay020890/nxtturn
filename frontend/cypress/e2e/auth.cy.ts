// C:\Users\Vinay\Project\frontend\cypress\e2e\auth.cy.ts
// ORIGINAL VERSION

describe('Authentication Flow', () => {

  // Create a new, isolated user just for this test suite
  const testUser = {
    username: `auth_test_user_${Date.now()}`,
    password: 'Airtel@123',
  };

  before(() => {
    // This command runs once before any tests in this file.
    // It creates the user needed for the login tests below.
    // NOTE: This relies on the older, non-consolidated test setup commands.
    cy.testSetup('create_user', testUser);
  });

  // A helper function that uses our isolated test user
  const login = () => {
    cy.get('#username').type(testUser.username);
    cy.get('#password').type(testUser.password);
    cy.get('button[type="submit"]').click();
    // Wait for the login to complete by checking for the logout button
    cy.get('[data-cy="logout-button"]').should('be.visible');
  };

  // --- Test Suite for Default/Mobile Viewport ---
  context('on a default (mobile/tablet) viewport', () => {
    
    beforeEach(() => {
      // Before each individual test, just visit the login page.
      cy.visit('/login');
    });

    it('successfully logs in and shows the main content, but hides sidebars', () => {
      login();
      cy.get('[data-cy="create-post-input"]').should('be.visible');
      cy.contains('My Groups').should('not.be.visible');
    });
  });

  // --- Test Suite for Wide/Desktop Viewport ---
  context('on a wide (desktop) viewport', () => {

    beforeEach(() => {
      // Before each test in this block, set the size and visit the page.
      cy.viewport('macbook-15');
      cy.visit('/login');
    });

    it('successfully logs in and displays both sidebars', () => {
      login();
      cy.get('[data-cy="create-post-input"]').should('be.visible');
      cy.contains('My Groups').should('be.visible');
      cy.contains('People You May Know').should('be.visible');
    });
  });
});