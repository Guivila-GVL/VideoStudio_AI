
    INSERT INTO shared_workflow ("workflowId", "projectId", role)
    SELECT 'hFjB4Zv88O8HIqd8', project.id, 'workflow:owner'
    FROM project LIMIT 1;
    