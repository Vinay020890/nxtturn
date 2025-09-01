// C:\Users\Vinay\Project\frontend\cypress\e2e\auth.cy.ts

describe('Authentication Flow', () => {

  // A helper function to avoid repeating the login steps
  const login = () => {
    cy.get('#username').type('abc1');
    cy.get('#password').type('Airtel@123');
    cy.get('button[type="submit"]').click();
    // Wait for the login to complete by checking for the logout button
    cy.contains('Logout').should('be.visible');
  };

  // --- Test Suite for Default/Mobile Viewport ---
  context('on a default (mobile/tablet) viewport', () => {
    
    beforeEach(() => {
      cy.visit('/');
    });

    it('successfully logs in and shows the main content, but hides sidebars', () => {
      login();

      // CORRECTED: Assert that the post creation input is visible by its placeholder
      cy.get('[placeholder*="What\'s on your mind?"]').should('be.visible');

      // CRITICAL ASSERTION: The "My Groups" link in the left sidebar
      // should NOT be visible on this screen size.
      cy.contains('My Groups').should('not.be.visible');
    });
  });

  // --- Test Suite for Wide/Desktop Viewport ---
  context('on a wide (desktop) viewport', () => {

    beforeEach(() => {
      cy.viewport('macbook-15');
      cy.visit('/');
    });

    it('successfully logs in and displays both sidebars', () => {
      login();

      // CORRECTED: Assert that the post creation input is visible by its placeholder
      cy.get('[placeholder*="What\'s on your mind?"]').should('be.visible');

      // CRITICAL ASSERTION: The "My Groups" link in the left sidebar
      // SHOULD BE visible on this screen size.
      cy.contains('My Groups').should('be.visible');

      // BONUS ASSERTION: Let's also check the right sidebar.
      cy.contains('People You May Know').should('be.visible');
    });
  });
});