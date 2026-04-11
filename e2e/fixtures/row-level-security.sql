--
-- Row Level Security (RLS) para JobBot
-- Asegura que los usuarios solo vean sus propios datos
--

-- Habilitar RLS en todas las tablas
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE cvs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE cv_analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;

-- Tabla: users
-- Usuarios solo pueden ver y modificar su propio perfil
CREATE POLICY "Users can only view own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can only update own profile"
  ON users FOR UPDATE
  USING (auth.uid() = id);

-- Tabla: cvs
-- Solo el dueño puede ver sus CVs
CREATE POLICY "Users can only access own CVs"
  ON cvs FOR ALL
  USING (auth.uid() = user_id);

-- Tabla: cv_analyses
-- Análisis vinculados al CV del usuario
CREATE POLICY "Users can only access own CV analyses"
  ON cv_analyses FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM cvs 
      WHERE cvs.id = cv_analyses.cv_id 
      AND cvs.user_id = auth.uid()
    )
  );

-- Tabla: applications
-- Postulaciones del usuario
CREATE POLICY "Users can only access own applications"
  ON applications FOR ALL
  USING (auth.uid() = user_id);

-- Tabla: user_settings
-- Configuración personal
CREATE POLICY "Users can only access own settings"
  ON user_settings FOR ALL
  USING (auth.uid() = user_id);

-- Tabla: credits
-- Créditos del usuario
CREATE POLICY "Users can only view own credits"
  ON credits FOR SELECT
  USING (auth.uid() = user_id);

-- Solo admins pueden modificar créditos
CREATE POLICY "Only admins can modify credits"
  ON credits FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM users 
      WHERE users.id = auth.uid() 
      AND users.role = 'admin'
    )
  );

-- Tabla: subscriptions
-- Suscripciones del usuario
CREATE POLICY "Users can only view own subscription"
  ON subscriptions FOR SELECT
  USING (auth.uid() = user_id);

-- Tabla: sessions
-- Sesiones del usuario
CREATE POLICY "Users can only view own sessions"
  ON sessions FOR SELECT
  USING (auth.uid() = user_id);

-- Política para admins (pueden ver todo)
CREATE POLICY "Admins can view all data"
  ON users FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM users u
      WHERE u.id = auth.uid()
      AND u.role = 'admin'
    )
  );

-- Función para verificar si es admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM users 
    WHERE users.id = auth.uid() 
    AND users.role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Índices para optimizar queries con RLS
CREATE INDEX IF NOT EXISTS idx_cvs_user_id ON cvs(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_cv_analyses_cv_id ON cv_analyses(cv_id);
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_user_id ON credits(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);

-- Trigger para audit logging
CREATE TABLE IF NOT EXISTS audit_log (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  table_name TEXT NOT NULL,
  record_id UUID,
  old_data JSONB,
  new_data JSONB,
  ip_address INET,
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Habilitar RLS en audit_log
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Solo admins pueden ver logs
CREATE POLICY "Only admins can view audit logs"
  ON audit_log FOR SELECT
  USING (is_admin());

-- Función para logging
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  IF (TG_OP = 'DELETE') THEN
    INSERT INTO audit_log (user_id, action, table_name, record_id, old_data)
    VALUES (auth.uid(), TG_OP, TG_TABLE_NAME, OLD.id, row_to_json(OLD));
    RETURN OLD;
  ELSIF (TG_OP = 'UPDATE') THEN
    INSERT INTO audit_log (user_id, action, table_name, record_id, old_data, new_data)
    VALUES (auth.uid(), TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(OLD), row_to_json(NEW));
    RETURN NEW;
  ELSIF (TG_OP = 'INSERT') THEN
    INSERT INTO audit_log (user_id, action, table_name, record_id, new_data)
    VALUES (auth.uid(), TG_OP, TG_TABLE_NAME, NEW.id, row_to_json(NEW));
    RETURN NEW;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Aplicar triggers de auditoría
CREATE TRIGGER cvs_audit
  AFTER INSERT OR UPDATE OR DELETE ON cvs
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER applications_audit
  AFTER INSERT OR UPDATE OR DELETE ON applications
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();

CREATE TRIGGER user_settings_audit
  AFTER INSERT OR UPDATE OR DELETE ON user_settings
  FOR EACH ROW EXECUTE FUNCTION audit_trigger();
