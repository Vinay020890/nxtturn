// C:\Users\Vinay\Project\frontend\cypress\e2e\multi-tab.cy.ts

describe('Multi-Tab Synchronization', () => {

  it('should log out the user and redirect if the auth token is removed', () => {
    // --- SETUP: Create a new, isolated user just for this test ---
    const testUser = {
      username: `multitab_user_${Date.now()}`,
      password: 'password123',
    };
    cy.testSetup('create_user', testUser);
    
    // Step 1: Programmatically log in AS THE NEW USER and visit the home page.
    cy.login(testUser.username, testUser.password);
    cy.visit('/');

    // Step 2: Assert we are in a logged-in state.
    cy.get('[data-cy="logout-button"]').should('be.visible');
    cy.url().should('not.include', '/login');

    // Step 3: Simulate another tab logging out by clearing localStorage.
    cy.log('Simulating logout from another tab by clearing the token.');
    cy.clearLocalStorage('authToken');

    // Step 4: A reload will trigger the auth check and reveal the logged-out state.
    cy.reload();

    // Step 5: Assert that the application has redirected to the login page.
    cy.url().should('include', '/login');
    cy.contains('Sign in to your account').should('be.visible');
  });
});