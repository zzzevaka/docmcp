import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { toast } from 'sonner'
import { AlertTriangle } from 'lucide-react'
import MainLayout from '../components/layout/MainLayout'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

function TeamDetail() {
  const { teamId } = useParams()
  const navigate = useNavigate()
  const [team, setTeam] = useState(null)
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(true)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showRemoveMemberModal, setShowRemoveMemberModal] = useState(false)
  const [memberToRemove, setMemberToRemove] = useState(null)
  const [isRemoving, setIsRemoving] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [editedTeamName, setEditedTeamName] = useState('')

  const fetchTeamData = async () => {
    try {
      const teamRes = await axios.get(`/api/v1/teams/${teamId}`, {
        withCredentials: true,
      })
      setTeam(teamRes.data)
      setMembers(teamRes.data.members || [])
    } catch (error) {
      console.error('Failed to fetch team data:', error)
      if (error.response?.status === 404) {
        toast.error('Team not found')
        navigate('/teams')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeamData()
  }, [teamId])

  const handleInviteUser = async (e) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return

    try {
      await axios.post(
        `/api/v1/teams/${teamId}/invitations`,
        { invitee_email: inviteEmail },
        { withCredentials: true }
      )
      setInviteEmail('')
      setShowInviteModal(false)
      toast.success('Invitation sent successfully!')
    } catch (error) {
      console.error('Failed to send invitation:', error)
      toast.error(error.response?.data?.detail || 'Failed to send invitation')
    }
  }

  const openRemoveMemberModal = (member) => {
    setMemberToRemove(member)
    setShowRemoveMemberModal(true)
  }

  const handleRemoveMember = async () => {
    if (!memberToRemove) return

    setIsRemoving(true)
    try {
      await axios.delete(`/api/v1/teams/${teamId}/members/${memberToRemove.id}`, {
        withCredentials: true,
      })
      setShowRemoveMemberModal(false)
      setMemberToRemove(null)
      fetchTeamData()
      toast.success('Member removed successfully')
    } catch (error) {
      console.error('Failed to remove member:', error)
      toast.error(error.response?.data?.detail || 'Failed to remove member')
    } finally {
      setIsRemoving(false)
    }
  }

  const handleEditTeam = async (e) => {
    e.preventDefault()
    if (!editedTeamName.trim()) return

    try {
      await axios.patch(
        `/api/v1/teams/${teamId}`,
        { name: editedTeamName },
        { withCredentials: true }
      )
      setShowEditDialog(false)
      fetchTeamData()
      toast.success('Team updated successfully!')
    } catch (error) {
      console.error('Failed to update team:', error)
      toast.error(error.response?.data?.detail || 'Failed to update team')
    }
  }

  const openEditDialog = () => {
    setEditedTeamName(team.name)
    setShowEditDialog(true)
  }

  if (loading) {
    return (
      <MainLayout activeTab="teams">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading team...</p>
          </div>
        </div>
      </MainLayout>
    )
  }

  if (!team) {
    return (
      <MainLayout activeTab="teams">
        <div className="text-center py-12">
          <p className="text-gray-600">Team not found</p>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout activeTab="teams">
      <div className="px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <div>
              <Breadcrumb className="mb-4">
                <BreadcrumbList>
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/teams">Teams</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbPage>{team.name}</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
            <div className="flex gap-2">
              <button
                onClick={openEditDialog}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
              >
                Edit Team
              </button>
              <button
                onClick={() => setShowInviteModal(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Invite Member
              </button>
            </div>
          </div>
        </div>

        {/* Members List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">
              Members ({members.length})
            </h2>
          </div>
          <div className="divide-y divide-gray-200">
            {members.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-600">
                No members yet. Invite someone to join this team!
              </div>
            ) : (
              members.map((member) => (
                <div
                  key={member.id}
                  className="px-6 py-4 flex justify-between items-center hover:bg-gray-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-medium">
                      {member.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {member.username}
                      </p>
                      <p className="text-sm text-gray-600">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {member.role && (
                      <span className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-full">
                        {member.role}
                      </span>
                    )}
                    <button
                      onClick={() => openRemoveMemberModal(member)}
                      className="px-3 py-1 text-sm text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

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

        {/* Edit Team Dialog */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Team</DialogTitle>
              <DialogDescription>
                Update the team name and settings.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleEditTeam}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Team Name
                </label>
                <input
                  type="text"
                  value={editedTeamName}
                  onChange={(e) => setEditedTeamName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter team name"
                  autoFocus
                />
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowEditDialog(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">Save Changes</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Remove Member Confirmation Modal */}
        {showRemoveMemberModal && memberToRemove && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
              <div className="flex items-start gap-3 mb-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Remove Member</h2>
                  <p className="mt-1 text-sm text-gray-600">
                    Are you sure you want to remove {memberToRemove.username} from this team?
                    They will lose access to all team resources.
                  </p>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowRemoveMemberModal(false)
                    setMemberToRemove(null)
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  disabled={isRemoving}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRemoveMember}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 disabled:opacity-50"
                  disabled={isRemoving}
                >
                  {isRemoving ? 'Removing...' : 'Remove'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}

export default TeamDetail
