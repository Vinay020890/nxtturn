// cypress/e2e/connections.cy.ts

describe('Connection Request System', () => {
  beforeEach(() => {
    cy.testSetup('create_two_users', {
      userA: { username: 'userA', password: 'password123' },
      userB: { username: 'userB', password: 'password123' },
    })
  })

  it('handles the full connection and follow lifecycle between two users', () => {
    // === PART 1: User A sends a request and follows User B ===
    cy.login('userA', 'password123')
    cy.visit('/profile/userB')

    // Action: Follow User B
    cy.intercept('GET', '**/api/users/userB/relationship/').as('getRelationshipAfterFollow')
    cy.get('[data-cy="follow-button"]').should('be.visible').click()
    cy.wait('@getRelationshipAfterFollow') // Wait for the state to be re-fetched
    cy.get('[data-cy="following-button"]').should('be.visible')

    // Action: Connect with User B
    cy.get('[data-cy="connect-button"]').should('be.visible').click()
    cy.get('[data-cy="pending-button"]').should('be.visible')

    cy.logout()
    cy.visit('/')
    cy.url().should('include', '/login')

    // === PART 2: User B accepts the request ===
    cy.login('userB', 'password123')
    cy.visit('/profile/userA')

    // Verify User B sees the correct buttons
    cy.get('[data-cy="accept-request-button"]').should('be.visible')
    cy.get('[data-cy="follow-back-button"]').should('be.visible')

    // Action: Accept Request
    cy.get('[data-cy="accept-request-button"]').click()

    // Assert the final connected state
    cy.get('[data-cy="connected-button"]').should('be.visible')
    cy.get('[data-cy="following-button"]').should('be.visible')

    // === PART 3: User B unfollows User A (breaking the connection) ===

    // 1. Set up an interception for the API call we are waiting for.
    cy.intercept('GET', '**/api/users/userA/relationship/').as('getRelationshipAfterUnfollow')

    // 2. Click the button that triggers the API call.
    cy.get('[data-cy="following-button"]').click()

    // 3. Explicitly wait for the intercepted API call to complete.
    cy.wait('@getRelationshipAfterUnfollow')

    // 4. Now that the UI has been updated with fresh data, we can safely make our assertions.
    cy.get('[data-cy="follow-back-button"]').should('be.visible')
    cy.get('[data-cy="connect-button"]').should('be.visible')
  })
})
