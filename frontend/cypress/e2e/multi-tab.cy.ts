// C:\Users\Vinay\Project\frontend\cypress\e2e\multi-tab.cy.ts

describe('Multi-Tab Synchronization', () => {

  it('should log out the user and redirect if the auth token is removed', () => {
    // Step 1: Programmatically log in and visit the home page.
    cy.login();
    cy.visit('/');

    // Step 2: Assert we are in a logged-in state.
    cy.contains('Logout').should('be.visible');
    cy.url().should('not.include', '/login');

    // Step 3: Simulate another tab logging out by clearing localStorage.
    cy.log('Simulating logout from another tab by clearing the token.');
    cy.clearLocalStorage('authToken');

    // Step 4: The app doesn't know about the change yet. A reload or navigation
    // will trigger the auth check and reveal the logged-out state.
    cy.reload();

    // Step 5: Assert that the application has redirected to the login page.
    cy.url().should('include', '/login');
    cy.contains('Sign in to your account').should('be.visible');
  });
});