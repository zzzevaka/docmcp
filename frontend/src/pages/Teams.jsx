import { useState, useEffect } from 'react'
import axios from 'axios'
import MainLayout from '../components/layout/MainLayout'

function Teams() {
  const [teams, setTeams] = useState([])
  const [pendingInvitations, setPendingInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [selectedTeamForInvite, setSelectedTeamForInvite] = useState(null)
  const [newTeamName, setNewTeamName] = useState('')
  const [inviteEmail, setInviteEmail] = useState('')

  const fetchData = async () => {
    try {
      const [teamsRes, invitationsRes] = await Promise.all([
        axios.get('/api/v1/teams/', { withCredentials: true }),
        axios.get('/api/v1/invitations/me', { withCredentials: true }),
      ])
      setTeams(teamsRes.data)
      setPendingInvitations(invitationsRes.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleCreateTeam = async (e) => {
    e.preventDefault()
    if (!newTeamName.trim()) return

    try {
      await axios.post(
        '/api/v1/teams/',
        { name: newTeamName },
        { withCredentials: true }
      )
      setNewTeamName('')
      setShowCreateModal(false)
      fetchData()
    } catch (error) {
      console.error('Failed to create team:', error)
      alert('Failed to create team')
    }
  }

  const handleInviteUser = async (e) => {
    e.preventDefault()
    if (!inviteEmail.trim() || !selectedTeamForInvite) return

    try {
      await axios.post(
        `/api/v1/teams/${selectedTeamForInvite}/invitations`,
        { invitee_email: inviteEmail },
        { withCredentials: true }
      )
      setInviteEmail('')
      setShowInviteModal(false)
      setSelectedTeamForInvite(null)
      alert('Invitation sent successfully!')
    } catch (error) {
      console.error('Failed to send invitation:', error)
      alert(error.response?.data?.detail || 'Failed to send invitation')
    }
  }

  const handleAcceptInvitation = async (invitationId) => {
    try {
      await axios.post(
        `/api/v1/invitations/${invitationId}/accept`,
        {},
        { withCredentials: true }
      )
      fetchData()
      alert('Invitation accepted!')
    } catch (error) {
      console.error('Failed to accept invitation:', error)
      alert('Failed to accept invitation')
    }
  }

  const handleRejectInvitation = async (invitationId) => {
    try {
      await axios.post(
        `/api/v1/invitations/${invitationId}/reject`,
        {},
        { withCredentials: true }
      )
      fetchData()
      alert('Invitation rejected')
    } catch (error) {
      console.error('Failed to reject invitation:', error)
      alert('Failed to reject invitation')
    }
  }

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading teams...</p>
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="px-4 py-6">
        {/* Pending Invitations Section */}
        {pendingInvitations.length > 0 && (
          <div className="mb-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Pending Invitations
            </h2>
            <div className="space-y-2">
              {pendingInvitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="bg-white p-4 rounded-lg shadow flex justify-between items-center"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {invitation.team_name}
                    </p>
                    <p className="text-sm text-gray-600">
                      Invited by {invitation.inviter_email}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleAcceptInvitation(invitation.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleRejectInvitation(invitation.id)}
                      className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Teams Section */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Teams</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Create Team
          </button>
        </div>

        {teams.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-600 mb-4">No teams yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Create Your First Team
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <div
                key={team.id}
                className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {team.name}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  Created {new Date(team.created_at).toLocaleDateString()}
                </p>
                <button
                  onClick={() => {
                    setSelectedTeamForInvite(team.id)
                    setShowInviteModal(true)
                  }}
                  className="w-full px-3 py-2 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
                >
                  Invite Member
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Create Team Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold mb-4">Create New Team</h2>
              <form onSubmit={handleCreateTeam}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Team Name
                  </label>
                  <input
                    type="text"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter team name"
                    autoFocus
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false)
                      setNewTeamName('')
                    }}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Invite User Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <h2 className="text-2xl font-bold mb-4">Invite Team Member</h2>
              <form onSubmit={handleInviteUser}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter email address"
                    autoFocus
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowInviteModal(false)
                      setInviteEmail('')
                      setSelectedTeamForInvite(null)
                    }}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Send Invitation
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}

export default Teams
