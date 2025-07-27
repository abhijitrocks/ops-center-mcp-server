#!/usr/bin/env python3
"""
Workbench Role Manager - Utility for managing roles within workbenches
Supports the 4 standard roles: Assessor, Reviewer, Team Lead, Viewer
"""

import sqlite3
from datetime import datetime
from typing import List, Dict, Optional


class WorkbenchRoleManager:
    """Manage roles within workbenches"""
    
    STANDARD_ROLES = ['Assessor', 'Reviewer', 'Team Lead', 'Viewer']
    
    def __init__(self, db_path: str = "ops_center.db"):
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def assign_workbench_role(self, agent: str, workbench_id: int, role: str, assigned_by: str = "system") -> bool:
        """Assign a role to an agent in a specific workbench"""
        if role not in self.STANDARD_ROLES:
            raise ValueError(f"Role must be one of: {self.STANDARD_ROLES}")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO workbench_roles (workbench_id, agent, role, assigned_by)
                VALUES (?, ?, ?, ?)
            ''', (workbench_id, agent, role, assigned_by))
            
            conn.commit()
            return True
            
        except sqlite3.IntegrityError:
            # Role already exists for this agent in this workbench
            return False
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def remove_workbench_role(self, agent: str, workbench_id: int, role: str) -> bool:
        """Remove a role from an agent in a specific workbench"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE workbench_roles 
                SET is_active = 0
                WHERE workbench_id = ? AND agent = ? AND role = ? AND is_active = 1
            ''', (workbench_id, agent, role))
            
            conn.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_agent_workbench_roles(self, agent: str) -> List[Dict]:
        """Get all workbench roles for a specific agent"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT w.name, wr.role, wr.workbench_id, wr.assigned_at
                FROM workbench_roles wr
                JOIN workbench w ON wr.workbench_id = w.id
                WHERE wr.agent = ? AND wr.is_active = 1
                ORDER BY w.name, wr.role
            ''', (agent,))
            
            return [
                {
                    'workbench_name': row[0],
                    'role': row[1],
                    'workbench_id': row[2],
                    'assigned_at': row[3]
                }
                for row in cursor.fetchall()
            ]
            
        finally:
            conn.close()
    
    def get_workbench_role_assignments(self, workbench_id: int) -> Dict:
        """Get all role assignments for a specific workbench"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get workbench info
            cursor.execute('SELECT name, description FROM workbench WHERE id = ?', (workbench_id,))
            wb_info = cursor.fetchone()
            
            if not wb_info:
                return None
            
            # Get role assignments
            cursor.execute('''
                SELECT agent, role, assigned_at, assigned_by
                FROM workbench_roles
                WHERE workbench_id = ? AND is_active = 1
                ORDER BY role, agent
            ''', (workbench_id,))
            
            assignments = cursor.fetchall()
            
            # Organize by role
            roles = {}
            for role in self.STANDARD_ROLES:
                roles[role] = []
            
            for agent, role, assigned_at, assigned_by in assignments:
                roles[role].append({
                    'agent': agent,
                    'assigned_at': assigned_at,
                    'assigned_by': assigned_by
                })
            
            return {
                'workbench_id': workbench_id,
                'workbench_name': wb_info[0],
                'description': wb_info[1],
                'roles': roles,
                'total_assignments': len(assignments),
                'missing_roles': [role for role in self.STANDARD_ROLES if not roles[role]]
            }
            
        finally:
            conn.close()
    
    def get_workbench_coverage_report(self) -> Dict:
        """Get a report of role coverage across all workbenches"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT w.id, w.name,
                       COUNT(CASE WHEN wr.role = 'Assessor' THEN 1 END) as assessors,
                       COUNT(CASE WHEN wr.role = 'Reviewer' THEN 1 END) as reviewers,
                       COUNT(CASE WHEN wr.role = 'Team Lead' THEN 1 END) as team_leads,
                       COUNT(CASE WHEN wr.role = 'Viewer' THEN 1 END) as viewers,
                       COUNT(wr.id) as total_assignments
                FROM workbench w
                LEFT JOIN workbench_roles wr ON w.id = wr.workbench_id AND wr.is_active = 1
                GROUP BY w.id, w.name
                ORDER BY w.id
            ''')
            
            workbenches = []
            total_gaps = 0
            
            for wb_id, wb_name, assessors, reviewers, team_leads, viewers, total in cursor.fetchall():
                coverage = {
                    'workbench_id': wb_id,
                    'workbench_name': wb_name,
                    'assessors': assessors,
                    'reviewers': reviewers,
                    'team_leads': team_leads,
                    'viewers': viewers,
                    'total_assignments': total,
                    'coverage_percentage': (total / len(self.STANDARD_ROLES)) * 100,
                    'gaps': len(self.STANDARD_ROLES) - min(total, len(self.STANDARD_ROLES))
                }
                
                workbenches.append(coverage)
                total_gaps += coverage['gaps']
            
            return {
                'workbenches': workbenches,
                'total_workbenches': len(workbenches),
                'total_role_gaps': total_gaps,
                'fully_covered_workbenches': len([w for w in workbenches if w['gaps'] == 0])
            }
            
        finally:
            conn.close()
    
    def suggest_role_assignments(self) -> List[Dict]:
        """Suggest role assignments to fill gaps"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get agents without any roles
            cursor.execute('''
                SELECT DISTINCT agent FROM usertaskinfo 
                WHERE agent NOT IN (
                    SELECT DISTINCT agent FROM workbench_roles WHERE is_active = 1
                )
            ''')
            
            available_agents = [row[0] for row in cursor.fetchall()]
            
            # Get workbenches with missing roles
            coverage = self.get_workbench_coverage_report()
            suggestions = []
            
            for wb in coverage['workbenches']:
                if wb['gaps'] > 0:
                    wb_details = self.get_workbench_role_assignments(wb['workbench_id'])
                    missing_roles = wb_details['missing_roles']
                    
                    for role in missing_roles:
                        if available_agents:
                            suggested_agent = available_agents[0]  # Simple assignment
                            suggestions.append({
                                'workbench_id': wb['workbench_id'],
                                'workbench_name': wb['workbench_name'],
                                'role': role,
                                'suggested_agent': suggested_agent,
                                'reason': f'Fill {role} gap in {wb["workbench_name"]}'
                            })
                        else:
                            suggestions.append({
                                'workbench_id': wb['workbench_id'],
                                'workbench_name': wb['workbench_name'],
                                'role': role,
                                'suggested_agent': None,
                                'reason': f'Need {role} for {wb["workbench_name"]} - no available agents'
                            })
            
            return suggestions
            
        finally:
            conn.close()


def main():
    """CLI interface for role management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Workbench Role Manager')
    parser.add_argument('action', choices=['assign', 'remove', 'list', 'coverage', 'suggest'])
    parser.add_argument('--agent', help='Agent name')
    parser.add_argument('--workbench-id', type=int, help='Workbench ID')
    parser.add_argument('--role', choices=WorkbenchRoleManager.STANDARD_ROLES, help='Role name')
    parser.add_argument('--assigned-by', default='cli', help='Who is making the assignment')
    
    args = parser.parse_args()
    manager = WorkbenchRoleManager()
    
    if args.action == 'assign':
        if not all([args.agent, args.workbench_id, args.role]):
            print("Error: assign requires --agent, --workbench-id, and --role")
            return
        
        success = manager.assign_workbench_role(args.agent, args.workbench_id, args.role, args.assigned_by)
        if success:
            print(f"✅ Assigned {args.role} role to {args.agent} in workbench {args.workbench_id}")
        else:
            print(f"⚠️  Role already exists or assignment failed")
    
    elif args.action == 'remove':
        if not all([args.agent, args.workbench_id, args.role]):
            print("Error: remove requires --agent, --workbench-id, and --role")
            return
        
        success = manager.remove_workbench_role(args.agent, args.workbench_id, args.role)
        if success:
            print(f"✅ Removed {args.role} role from {args.agent} in workbench {args.workbench_id}")
        else:
            print(f"⚠️  Role not found or removal failed")
    
    elif args.action == 'list':
        if args.agent:
            roles = manager.get_agent_workbench_roles(args.agent)
            print(f"Roles for {args.agent}:")
            for role in roles:
                print(f"  • {role['workbench_name']}: {role['role']}")
        elif args.workbench_id:
            assignments = manager.get_workbench_role_assignments(args.workbench_id)
            if assignments:
                print(f"Assignments for {assignments['workbench_name']}:")
                for role, agents in assignments['roles'].items():
                    if agents:
                        for agent_info in agents:
                            print(f"  • {role}: {agent_info['agent']}")
                    else:
                        print(f"  • {role}: (vacant)")
        else:
            print("Error: list requires either --agent or --workbench-id")
    
    elif args.action == 'coverage':
        report = manager.get_workbench_coverage_report()
        print("Workbench Role Coverage Report:")
        for wb in report['workbenches']:
            print(f"  {wb['workbench_name']}: {wb['coverage_percentage']:.0f}% coverage ({wb['gaps']} gaps)")
    
    elif args.action == 'suggest':
        suggestions = manager.suggest_role_assignments()
        print("Role Assignment Suggestions:")
        for suggestion in suggestions:
            if suggestion['suggested_agent']:
                print(f"  • Assign {suggestion['suggested_agent']} as {suggestion['role']} in {suggestion['workbench_name']}")
            else:
                print(f"  • Need {suggestion['role']} for {suggestion['workbench_name']} - no available agents")


if __name__ == "__main__":
    main()