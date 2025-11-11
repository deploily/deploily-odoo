from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Liste déroulante
    x_training_source = fields.Selection(
        [
            ('Site web', 'Site web'),
            ('LinkedIn', 'LinkedIn'),
            ('Facebook', 'Facebook'),
            ('Instagram', 'Instagram'),
            ('YouTube', 'YouTube'),
            ('Autres', 'Autres'),
        ],
        string="Où avez-vous entendu parler de cette formation",
    )

    x_status = fields.Selection(
        [
            ('specialist', 'Médecin spécialiste'),
            ('general', 'Médecin généraliste'),
            ('resident', 'Résident'),
            ('pharmacist', 'Pharmacien'),
            ('dentist', 'Chirurgien dentiste'),
            ('biologist', 'Biologiste'),
            ('veterinarian', 'Vétérinaire'),
            ('nutritionist', 'Nutritionniste'),
            ('nurse', 'Infirmier'),
            ('other', 'Autres'),
        ],
        string="Statut",
    )