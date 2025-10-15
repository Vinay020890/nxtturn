// C:\Users\Vinay\Project\frontend\cypress\e2e\connections.cy.ts

describe('Connection Request System', () => {
  const apiBaseUrl = Cypress.env('VITE_API_BASE_URL')

  beforeEach(() => {
    cy.testSetup('create_two_users', {
      userA: { username: 'userA', password: 'password123' },
      userB: { username: 'userB', password: 'password123' },
    })
  })

  it('handles the full connection and follow lifecycle between two users', () => {
    // === PART 1: User A sends a connection request to User B ===
    cy.login('userA', 'password123')

    // --- FIX: Intercept the main profile endpoint now ---
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userB/`).as('getProfileB')
    cy.visit('/profile/userB')
    cy.wait('@getProfileB') // Wait for the profile to load

    // ASSERT initial state
    cy.get('[data-cy="connect-button"]').should('be.visible')
    cy.get('[data-cy="follow-button"]').should('be.visible')

    // ACTION: User A clicks "Connect"
    cy.intercept('POST', `${apiBaseUrl}/api/connections/requests/`).as('sendRequest')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userB/`).as('getProfileB_AfterConnect') // Re-intercept for the refresh
    cy.get('[data-cy="connect-button"]').click()
    cy.wait(['@sendRequest', '@getProfileB_AfterConnect'])

    // ASSERT: Button state changes to "Pending"
    cy.get('[data-cy="pending-button"]').should('be.visible')
    cy.logout()

    // === PART 2: User B accepts the request ===
    cy.login('userB', 'password123')

    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA')
    cy.visit('/profile/userA')
    cy.wait('@getProfileA')

    // ASSERT: User B sees "Accept Request"
    cy.get('[data-cy="accept-request-button"]').should('be.visible')

    // ACTION: User B clicks "Accept Request"
    cy.intercept('POST', `${apiBaseUrl}/api/users/userA/accept-request/`).as('acceptRequest')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA_AfterAccept')
    cy.get('[data-cy="accept-request-button"]').click()
    cy.wait(['@acceptRequest', '@getProfileA_AfterAccept'])

    // ASSERT: Final connected state is visible
    cy.get('[data-cy="connected-button"]').should('be.visible')
    // The secondary follow button area should now be gone
    cy.get('[data-cy="follow-button"]').should('not.exist')

    // === PART 3: User B disconnects from User A ===
    // ACTION: User B clicks "Connected" to disconnect
    cy.intercept('DELETE', `${apiBaseUrl}/api/users/userA/follow/`).as('unfollowUser')
    cy.intercept('GET', `${apiBaseUrl}/api/profiles/userA/`).as('getProfileA_AfterDisconnect')
    // The "Connected" button is now the "Disconnect" button
    cy.get('[data-cy="disconnect-button"]').click()
    cy.wait(['@unfollowUser', '@getProfileA_AfterDisconnect'])

    // ASSERT: State reverts to "not_connected"
    cy.get('[data-cy="connect-button"]').should('be.visible')
    cy.get('[data-cy="follow-button"]').should('be.visible')
  })
})
