
    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT 'FomTQNzqTn235i6w', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    